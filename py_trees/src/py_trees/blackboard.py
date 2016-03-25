#!/usr/bin/env python
#
# License: BSD
#   https://raw.github.com/yujinrobot/gopher_crazy_hospital/license/LICENSE
#
##############################################################################
# Documentation
##############################################################################

"""
.. module:: common
   :platform: Unix
   :synopsis: Shared data storage for py_trees behaviours.

----

"""

##############################################################################
# Imports
##############################################################################

from . import behaviours

from .common import Status
from .behaviour import Behaviour
import rocon_console.console as console

##############################################################################
# Classes
##############################################################################


class Blackboard(object):
    """
      Borg style data store for sharing amongst behaviours.

      http://code.activestate.com/recipes/66531-singleton-we-dont-need-no-stinkin-singleton-the-bo/

      To register new variables on the blackboard, just promiscuously do so from instantiations of
      the borg. e.g.

      @code
        blackboard = Blackboard()
        blackboard.foo = "bar"
      @endcode

      This has the problem that it could collide with an existing key that is being used by another
      behaviour (independently). If we wanted to safeguard against these collisions, we should
      think some more. Perhaps overriding __setattr__ to do the check for us could work, but it means
      it will trigger the check even when you are setting the variable. Probably we want a much
      more complex base borg object to enable this kind of rigour.

      Convenience or Rigour?
    """
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def set(self, name, value, overwrite=True):
        """
        For when you only have strings to identify and access the blackboard variables, this
        provides a convenient setter.
        """
        if not overwrite:
            try:
                getattr(self, name)
                return False
            except AttributeError:
                pass
        setattr(self, name, value)
        return True

    def get(self, name):
        """
        For when you only have strings to identify and access the blackboard variables,
        this provides a convenient accessor.
        """
        try:
            return getattr(self, name)
        except AttributeError:
            return None

    def __str__(self):
        s = console.green + type(self).__name__ + "\n" + console.reset
        max_length = 0
        for k in self.__dict__.keys():
            max_length = len(k) if len(k) > max_length else max_length
        for key, value in self.__dict__.iteritems():
            if value is None:
                value_string = "-"
                s += console.cyan + "  " + '{0: <{1}}'.format(key, max_length + 1) + console.reset + ": " + console.yellow + "%s\n" % (value_string) + console.reset
            else:
                lines = ("%s" % value).split('\n')
                if len(lines) > 1:
                    s += console.cyan + "  " + '{0: <{1}}'.format(key, max_length + 1) + console.reset + ":\n"
                    for line in lines:
                        s += console.yellow + "    %s\n" % line + console.reset
                else:
                    s += console.cyan + "  " + '{0: <{1}}'.format(key, max_length + 1) + console.reset + ": " + console.yellow + "%s\n" % (value) + console.reset
        s += console.reset
        return s


class ClearBlackboardVariable(behaviours.Success):
    """
    Clear the specified value from the blackboard.
    """
    def __init__(self,
                 name="Clear Blackboard Variable",
                 variable_name="dummy",
                 ):
        """
        :param name: name of the behaviour
        :param variable_name: name of the variable to clear
        """
        super(ClearBlackboardVariable, self).__init__(name)
        self.variable_name = variable_name

    def initialise(self):
        self.blackboard = Blackboard()
        try:
            delattr(self.blackboard, self.variable_name)
        except AttributeError:
            pass


class SetBlackboardVariable(behaviours.Success):
    """
    Set the specified variable on the blackboard.
    Usually we set variables from inside other behaviours, but can
    be convenient to set them from a behaviour of their own sometimes so you
    don't get blackboard logic mixed up with more atomic behaviours.

    .. todo:: overwrite option, leading to possible failure/success logic.
    """
    def __init__(self,
                 name="Set Blackboard Variable",
                 variable_name="dummy",
                 variable_value=None
                 ):
        """
        :param name: name of the behaviour
        :param variable_name: name of the variable to set
        :param value_name: value of the variable to set
        """
        super(SetBlackboardVariable, self).__init__(name)
        self.variable_name = variable_name
        self.variable_value = variable_value

    def initialise(self):
        self.blackboard = Blackboard()
        self.blackboard.set(self.variable_name, self.variable_value, overwrite=True)


class CheckBlackboardVariable(Behaviour):
    """
    Check the blackboard to see if it has a specific variable
    and optionally whether that variable has a specific value.
    """
    def __init__(self,
                 name,
                 variable_name="dummy",
                 expected_value=None,
                 invert=False
                 ):
        """
        :param name: name of the behaviour
        :param variable_name: name of the variable to check
        :param expected_value: expected value of the variable, if None it will only check for existence
        :param invert: if true, check that the value of the variable is != expected_value, rather than ==
        """
        super(CheckBlackboardVariable, self).__init__(name)
        self.blackboard = Blackboard()
        self.variable_name = variable_name
        self.expected_value = expected_value
        # if the user sets the expected value, we check it
        self.invert = invert

    def update(self):
        # existence failure check
        if not hasattr(self.blackboard, self.variable_name):
            self.feedback_message = 'blackboard variable {0} did not exist'.format(self.variable_name)
            return Status.FAILURE

        # if existence check required only
        if self.expected_value is None:
            self.feedback_message = "'%s' exists on the blackboard (as required)" % self.variable_name
            return Status.SUCCESS

        # expected value matching
        value = getattr(self.blackboard, self.variable_name)
        matched_expected = (value == self.expected_value)

        # result
        if self.invert:
            result = not matched_expected
            if result:
                self.feedback_message = "'%s' did not match expected value (as required) [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                return Status.SUCCESS
            else:
                self.feedback_message = "'%s' matched expected value (required otherwise) [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                return Status.FAILURE
        else:
            if matched_expected:
                self.feedback_message = "'%s' matched expected value (as required) [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                return Status.SUCCESS
            else:
                self.feedback_message = "'%s' did not match expected value (required otherwise) [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                return Status.FAILURE
