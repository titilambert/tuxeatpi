"""Voice component"""

import importlib
from queue import Empty
from multiprocessing import Process


class Actionner(Process):
    """Define voices component

    For now voice use Nuance communications services
    """
    def __init__(self, tuxdroid):
        Process.__init__(self)
        # Set logger
        self.logger = tuxdroid.logger.getChild("Actionner")
        self.logger.debug("Initialization")
        # Set queue
        self.tuxdroid = tuxdroid
        self.tts_queue = tuxdroid.tts_queue
        self.nlu_queue = tuxdroid.nlu_queue
        self.action_queue = tuxdroid.action_queue
        # Init private attributes
        # self._settings = tuxdroid.settings
        self._must_run = False

    def _say(self, text):
        """Put text in tts queue"""
        self.tts_queue.put(text)

    def stop(self):
        """Stop process"""
        self._must_run = False
        self.terminate()

    def run(self):
        """Action to launch"""
        self._must_run = True
        while self._must_run:
            try:
                action_dict = self.action_queue.get(timeout=1)
            except Empty:
                self.logger.debug("No action received")
                continue
            # Reload config from file because we are in an other Process
            self.tuxdroid.settings.reload()

            self.logger.debug("Action received: {}".format(action_dict))
            self._actionning = True
            # Get action module
            module_action = action_dict['action']
            # Get action class
            class_action = action_dict['action'].capitalize() + "Action"
            # Get action method
            method_name = action_dict['method']
            # Get action
            action_args = action_dict['args']
            # Get args
            action_args['print_it'] = action_dict.get('print_it', False)
            action_args['text_it'] = action_dict.get('text_it', False)
            action_args['say_it'] = action_dict.get('say_it', False)
            # Get module
            full_module_action = importlib.import_module('.'.join(('tuxeatpi',
                                                                   'actions',
                                                                   module_action)))
            # Get object
            action_obj = getattr(full_module_action, class_action)(self.tuxdroid)
            # get method
            action_func = getattr(action_obj, method_name)
            self.logger.debug("Action %s.%s.%s with args %s", module_action,
                              class_action, method_name, action_args)
            self.logger.debug("Action %s with args %s", action_func, action_args)
            # run action
            # TODO put it in coroutine or thread
            # in order to get this call none-blocking
            action_func(**action_args)
            self._actionning = False
            # TODO Delete action obj ?


class ActionError(Exception):
    """Base class for action exceptions"""
    pass
