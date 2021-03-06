from MpfTestCase import MpfTestCase


class TestEventManager(MpfTestCase):

    def __init__(self, test_map):
        super(TestEventManager, self).__init__(test_map)
        self._handler1_args = tuple()
        self._handler1_kwargs = dict()
        self._handler1_called = 0
        self._handler2_args = tuple()
        self._handler2_kwargs = dict()
        self._handler2_called = 0
        self._handlers_called = list()
        self._handler_returns_false_args = tuple()
        self._handler_returns_false_kwargs = dict()
        self._handler_returns_false_called = 0
        self._relay1_called = 0
        self._relay2_called = 0
        self._relay_callback_args = tuple()
        self._relay_callback_kwargs = dict()
        self._relay_callback_called = 0
        self._callback_args = tuple()
        self._callback_kwargs = dict()
        self._callback_called = 0
        self._queue = None
        self._queue_callback_args = tuple()
        self._queue_callback_kwargs = dict()
        self._queue_callback_called = 0

    def getConfigFile(self):
        return 'test_event_manager.yaml'

    def getMachinePath(self):
        return '../tests/machine_files/event_manager/'

    def event_handler1(self, *args, **kwargs):
        self._handler1_args = args
        self._handler1_kwargs = kwargs
        self._handler1_called += 1
        self._handlers_called.append(self.event_handler1)

    def event_handler2(self, *args, **kwargs):
        self._handler2_args = args
        self._handler2_kwargs = kwargs
        self._handler2_called += 1
        self._handlers_called.append(self.event_handler2)

    def event_handler_returns_false(self, *args, **kwargs):
        self._handler_returns_false_args = args
        self._handler_returns_false_kwargs = kwargs
        self._handler_returns_false_called += 1
        self._handlers_called.append(self.event_handler_returns_false)

        return False

    def event_handler_relay1(self, relay_test):
        self._relay1_called += 1
        self._handlers_called.append(self.event_handler_relay1)

        return {'relay_test': relay_test}

    def event_handler_relay2(self, relay_test):
        self._relay2_called += 1
        self._handlers_called.append(self.event_handler_relay2)

        return {'relay_test': relay_test-1}

    def callback(self, *args, **kwargs):
        self._callback_args = args
        self._callback_kwargs = kwargs
        self._callback_called += 1
        self._handlers_called.append(self.callback)

    def relay_callback(self, *args, **kwargs):
        self._relay_callback_args = args
        self._relay_callback_kwargs = kwargs
        self._relay_callback_called += 1
        self._handlers_called.append(self.relay_callback)

    def event_handler_calls_second_event(self):
        self.machine.events.post('second_event')
        self._handlers_called.append(self.event_handler_calls_second_event)

    def event_handler_add_queue(self, queue):
        self._handlers_called.append(self.event_handler_add_queue)
        self._queue = queue
        self._queue.wait()

    def event_handler_add_quick_queue(self, queue):
        self._handlers_called.append(self.event_handler_add_quick_queue)
        self._queue = queue
        self._queue.wait()
        self._queue.clear()

    def event_handler_clear_queue(self):
        self._handlers_called.append(self.event_handler_clear_queue)
        self._queue.clear()

    def queue_callback(self, *args, **kwargs):
        self._queue_callback_args = args
        self._queue_callback_kwargs = kwargs
        self._queue_callback_called += 1
        self._handlers_called.append(self.queue_callback)

    def test_event(self):
        # tests that a handler responds to a regular event post
        self.machine.events.add_handler('test_event', self.event_handler1)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

    def test_event_with_kwargs(self):
        # test that a kwarg can be passed to a handler which is registered for
        # a regular event post
        self.machine.events.add_handler('test_event', self.event_handler1)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event', test1='test1')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals({'test1': 'test1'}, self._handler1_kwargs)

    def test_event_with_callback(self):
        # test that a callback is called when the event is done
        self.machine.events.add_handler('test_event', self.event_handler1)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event', test1='test1',
                                 callback=self.callback)
        self.advance_time_and_run(1)

        self.assertEquals(1, self._callback_called)

    def test_nested_callbacks(self):
        # tests that an event handlers which posts another event has that event
        # handled before the first event's callback is called

        self.machine.events.add_handler('test_event',
                                        self.event_handler_calls_second_event)
        self.machine.events.add_handler('second_event', self.event_handler1)

        self.advance_time_and_run(1)

        self.machine.events.post('test_event', callback=self.callback)
        self.advance_time_and_run(1)

        self.assertEquals(self._handlers_called[0],
                          self.event_handler_calls_second_event)
        self.assertEquals(self._handlers_called[1],
                          self.event_handler1)
        self.assertEquals(self._handlers_called[2],
                          self.callback)

    def test_event_handler_priorities(self):
        # tests that handler priorities work. The second handler should be
        # called first because it's a higher priority even though it's
        # registered second
        self.machine.events.add_handler('test_event', self.event_handler1,
                                        priority=100)
        self.machine.events.add_handler('test_event', self.event_handler2,
                                        priority=200)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)
        self.assertEquals(1, self._handler2_called)
        self.assertEquals(tuple(), self._handler2_args)
        self.assertEquals(dict(), self._handler2_kwargs)

        self.assertEquals(self._handlers_called[0], self.event_handler2)
        self.assertEquals(self._handlers_called[1], self.event_handler1)

    def test_remove_handler_by_handler(self):
        # tests that a handler can be removed by passing the handler to remove
        self.machine.events.add_handler('test_event', self.event_handler1)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        self.machine.events.remove_handler(self.event_handler1)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

    def test_remove_handler_by_event(self):
        # tests that a handler can be removed by a handler/event combo, and
        # that only that handler/event combo is removed
        self.machine.events.add_handler('test_event1', self.event_handler1)
        self.machine.events.add_handler('test_event2', self.event_handler1)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event1')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        # should not remove handler since this is the wrong event
        self.machine.events.remove_handler_by_event('test_event3',
                                                    self.event_handler1)

        self.machine.events.post('test_event1')
        self.advance_time_and_run(1)

        self.assertEquals(2, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        # remove handler for this event
        self.machine.events.remove_handler_by_event('test_event1',
                                                    self.event_handler1)

        self.machine.events.post('test_event1')
        self.advance_time_and_run(1)

        # results should be the same as above since this handler was removed
        self.assertEquals(2, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        self.machine.events.post('test_event2')
        self.advance_time_and_run(1)

        # results should be the same as above since this handler was removed
        self.assertEquals(3, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

    def test_remove_handler_by_key(self):
        # tests that a handler responds to a regular event post
        key = self.machine.events.add_handler('test_event',
                                              self.event_handler1)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        self.machine.events.remove_handler_by_key(key)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

    def test_remove_handlers_by_keys(self):
        # tests that multiple handlers can be removed by an iterable keys list
        keys = list()

        keys.append(self.machine.events.add_handler('test_event1',
                                                    self.event_handler1))
        keys.append(self.machine.events.add_handler('test_event2',
                                                    self.event_handler2))
        self.machine.events.post('test_event1')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        self.machine.events.post('test_event2')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler2_called)
        self.assertEquals(tuple(), self._handler2_args)
        self.assertEquals(dict(), self._handler2_kwargs)

        self.machine.events.remove_handlers_by_keys(keys)

        # post events again and handlers should not be called again
        self.machine.events.post('test_event1')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)

        self.machine.events.post('test_event2')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler2_called)
        self.assertEquals(tuple(), self._handler2_args)
        self.assertEquals(dict(), self._handler2_kwargs)

    def test_does_event_exist(self):
        self.machine.events.add_handler('test_event', self.event_handler1)

        self.assertEquals(True,
                          self.machine.events.does_event_exist('test_event'))
        self.assertEquals(False,
                          self.machine.events.does_event_exist('test_event1'))

    def test_regular_event_with_false_return(self):
        # tests that regular events process all handlers even if one returns
        # False

        self.machine.events.add_handler('test_event', self.event_handler1,
                                        priority=100)
        self.machine.events.add_handler('test_event',
                                        self.event_handler_returns_false,
                                        priority=200)
        self.advance_time_and_run(1)

        self.machine.events.post('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(1, self._handler_returns_false_called)

        self.assertEquals(self._handlers_called[0],
                          self.event_handler_returns_false)
        self.assertEquals(self._handlers_called[1], self.event_handler1)

    def test_post_boolean(self):
        # tests that a boolean event works

        self.machine.events.add_handler('test_event', self.event_handler1,
                                        priority=100)
        self.machine.events.add_handler('test_event', self.event_handler2,
                                        priority=200)
        self.advance_time_and_run(1)

        self.machine.events.post_boolean('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(1, self._handler1_called)
        self.assertEquals(tuple(), self._handler1_args)
        self.assertEquals(dict(), self._handler1_kwargs)
        self.assertEquals(1, self._handler2_called)
        self.assertEquals(tuple(), self._handler2_args)
        self.assertEquals(dict(), self._handler2_kwargs)

        self.assertEquals(self._handlers_called[0], self.event_handler2)
        self.assertEquals(self._handlers_called[1], self.event_handler1)

    def test_boolean_event_with_false_return(self):
        # tests that regular events process all handlers even if one returns
        # False

        self.machine.events.add_handler('test_event', self.event_handler1,
                                        priority=100)
        self.machine.events.add_handler('test_event',
                                        self.event_handler_returns_false,
                                        priority=200)
        self.advance_time_and_run(1)

        self.machine.events.post_boolean('test_event')
        self.advance_time_and_run(1)

        self.assertEquals(0, self._handler1_called)
        self.assertEquals(1, self._handler_returns_false_called)

        self.assertEquals(self._handlers_called[0],
                          self.event_handler_returns_false)

        self.assertEquals(1, len(self._handlers_called))

    def test_relay_event(self):
        # tests that a relay event works by passing a value

        self.machine.events.add_handler('test_event',
                                        self.event_handler_relay1,
                                        priority=200)

        self.advance_time_and_run(1)

        self.machine.events.post_relay('test_event', relay_test=1,
                                       callback=self.relay_callback)
        self.advance_time_and_run(1)

        self.assertEquals(1, self._relay1_called)
        self.assertEquals(1, self._relay_callback_called)

        assert 'relay_test' in self._relay_callback_kwargs
        assert self._relay_callback_kwargs['relay_test'] == 1

    def test_relay_event_handler_changes_value(self):
        # tests that a relay event works by passing a value to a handler that
        # changes that value

        self.machine.events.add_handler('test_event',
                                        self.event_handler_relay1,
                                        priority=200)
        self.machine.events.add_handler('test_event',
                                        self.event_handler_relay2,
                                        priority=100)
        self.advance_time_and_run(1)

        self.machine.events.post_relay('test_event', relay_test=1,
                                       callback=self.relay_callback)
        self.advance_time_and_run(1)

        self.assertEquals(1, self._relay1_called)
        self.assertEquals(1, self._relay2_called)
        self.assertEquals(1, self._relay_callback_called)

        assert 'relay_test' in self._relay_callback_kwargs
        self.assertEquals(self._relay_callback_kwargs['relay_test'], 0)

    def test_queue(self):
        # tests that a queue event works by registering and clearing a queue

        self.machine.events.add_handler('test_event',
                                        self.event_handler_add_queue)

        self.advance_time_and_run(1)

        self.machine.events.post_queue('test_event',
                                       callback=self.queue_callback)
        self.advance_time_and_run(1)

        self.assertEquals(
            self._handlers_called.count(self.event_handler_add_queue), 1)
        self.assertEquals(self._handlers_called.count(self.queue_callback), 0)
        self.assertEquals(False, self._queue.is_empty())

        self.event_handler_clear_queue()

        self.assertEquals(self._handlers_called.count(self.queue_callback), 1)
        self.assertEquals(True, self._queue.is_empty())

    def test_queue_kill(self):
        # tests that a queue event can be killed without the callback being
        # called

        self.machine.events.add_handler('test_event',
                                        self.event_handler_add_queue)

        self.advance_time_and_run(1)

        self.machine.events.post_queue('test_event',
                                       callback=self.queue_callback)
        self.advance_time_and_run(1)

        self.assertEquals(
            self._handlers_called.count(self.event_handler_add_queue), 1)
        self.assertEquals(self._handlers_called.count(self.queue_callback), 0)

        self._queue.kill()
        self.advance_time_and_run(1)

        self.assertEquals(self._handlers_called.count(self.queue_callback), 0)

    def test_queue_event_with_no_queue(self):
        # tests that a queue event works and the callback is called right away
        # if no handlers request a wait

        self.machine.events.add_handler('test_event', self.event_handler1)

        self.advance_time_and_run(1)

        self.machine.events.post_queue('test_event',
                                       callback=self.queue_callback)

        self.advance_time_and_run(1)

        self.assertEquals(self._handlers_called.count(self.event_handler1), 1)
        self.assertEquals(self._handlers_called.count(self.queue_callback), 1)

    def test_queue_event_with_handler_that_returns_false(self):
        # tests that a queue event stops processing additional handlers if one
        # of the handlers returns false

        self.machine.events.add_handler('test_event',
                                        self.event_handler_add_queue,
                                        priority=100)
        self.machine.events.add_handler('test_event',
                                        self.event_handler_returns_false,
                                        priority=200)

        self.advance_time_and_run(1)

        self.machine.events.post_queue('test_event',
                                       callback=self.queue_callback)
        self.advance_time_and_run(1)

        self.assertEquals(
            self._handlers_called.count(self.event_handler_returns_false), 1)
        self.assertEquals(
            self._handlers_called.count(self.event_handler_add_queue), 0)
        self.assertEquals(self._handlers_called.count(self.queue_callback), 1)
        self.assertEquals(self._queue_callback_kwargs, {'ev_result': False})

    def test_queue_event_with_quick_queue_clear(self):
        # tests that a queue event that quickly creates and clears a queue

        self.machine.events.add_handler('test_event',
                                        self.event_handler_add_quick_queue)

        self.advance_time_and_run(1)

        self.machine.events.post_queue('test_event',
                                       callback=self.queue_callback)
        self.advance_time_and_run(1)

        self.assertEquals(
            self._handlers_called.count(self.event_handler_add_quick_queue), 1)

        self.assertEquals(self._handlers_called.count(self.queue_callback), 1)
        self.assertEquals(True, self._queue.is_empty())

    def test_queue_event_with_no_registered_handlers(self):
        # tests that a queue event callback is called works even if there are
        # not registered handlers for that event

        self.machine.events.post_queue('test_event',
                                       callback=self.queue_callback)
        self.advance_time_and_run(1)

        self.assertEquals(self._handlers_called.count(self.queue_callback), 1)
        self.assertIsNone(self._queue)