import unittest

from mpf.system.machine import MachineController
from MpfTestCase import MpfTestCase
from mock import MagicMock
import time

class TestBallDeviceTriggerEvents(MpfTestCase):

    def __init__(self, test_map):
        super(TestBallDeviceTriggerEvents, self).__init__(test_map)
        self._captured = 0
        self._enter = 0
        self._missing = 0
        self._requesting = 0
        self._queue = False

    def getConfigFile(self):
        return 'test_ball_device_trigger_events.yaml'

    def getMachinePath(self):
        return '../tests/machine_files/ball_device/'

    def _missing_ball(self):
        self._missing += 1

    def _requesting_ball(self, balls, **kwargs):
        self._requesting += balls

    def _ball_enter(self, new_balls, unclaimed_balls, **kwargs):
        self._enter += new_balls

    def _captured_from_pf(self, balls, **kwargs):
        self._captured += balls

    def test_manual_successful_eject_to_pf(self):
        coil1 = self.machine.coils['eject_coil1']
        coil2 = self.machine.coils['eject_coil2']
        device1 = self.machine.ball_devices['test_trough']
        device2 = self.machine.ball_devices['test_launcher']
        playfield = self.machine.ball_devices['playfield']

        self.machine.events.add_handler('balldevice_captured_from_playfield', self._captured_from_pf)
        self.machine.events.add_handler('balldevice_1_ball_missing', self._missing_ball)
        self._enter = 0
        self._captured = 0
        self._missing = 0

        # add an initial ball to trough
        self.machine.switch_controller.process_switch("s_ball_switch1", 1)
        self.advance_time_and_run(1)
        self.assertEquals(1, self._captured)
        self._captured = 0
        self.assertEquals(0, playfield.balls)

        # it should keep the ball
        coil1.pulse = MagicMock()
        coil2.pulse = MagicMock()
        self.assertEquals(1, device1.balls)
        assert not coil1.pulse.called
        assert not coil2.pulse.called

        # request an ball
        playfield.add_ball(player_controlled=True)
        self.advance_time_and_run(1)

        # trough eject
        coil1.pulse.assert_called_once_with()
        assert not coil2.pulse.called

        self.machine.switch_controller.process_switch("s_ball_switch1", 0)
        self.advance_time_and_run(1)
        self.assertEquals(0, device1.balls)

        # launcher receives but waits for player to eject
        self.machine.switch_controller.process_switch("s_ball_switch_launcher", 1)
        self.advance_time_and_run(1)
        self.assertEquals(1, device2.balls)

        coil1.pulse.assert_called_once_with()
        assert not coil2.pulse.called

        # player shoots the ball
        self.machine.switch_controller.process_switch("s_launch", 1)
        self.advance_time_and_run(1)
        self.machine.switch_controller.process_switch("s_launch", 0)
        self.advance_time_and_run(1)

        self.machine.switch_controller.process_switch("s_ball_switch_launcher", 0)
        self.advance_time_and_run(1)
        self.assertEquals(0, device2.balls)

        self.machine.switch_controller.process_switch("s_playfield", 1)
        self.advance_time_and_run(0.1)
        self.machine.switch_controller.process_switch("s_playfield", 0)
        self.advance_time_and_run(1)

        self.assertEquals(1, playfield.balls)
        self.assertEquals(0, self._captured)
        self.assertEquals(0, self._missing)

    def test_manual_with_retry_to_pf(self):
        coil1 = self.machine.coils['eject_coil1']
        coil2 = self.machine.coils['eject_coil2']
        device1 = self.machine.ball_devices['test_trough']
        device2 = self.machine.ball_devices['test_launcher']
        playfield = self.machine.ball_devices['playfield']

        self.machine.events.add_handler('balldevice_captured_from_playfield', self._captured_from_pf)
        self.machine.events.add_handler('balldevice_1_ball_missing', self._missing_ball)
        self._enter = 0
        self._captured = 0
        self._missing = 0

        # add an initial ball to trough
        self.machine.switch_controller.process_switch("s_ball_switch1", 1)
        self.advance_time_and_run(1)
        self.assertEquals(1, self._captured)
        self._captured = 0
        self.assertEquals(0, playfield.balls)

        # it should keep the ball
        coil1.pulse = MagicMock()
        coil2.pulse = MagicMock()
        self.assertEquals(1, device1.balls)
        assert not coil1.pulse.called
        assert not coil2.pulse.called

        # request an ball
        playfield.add_ball(player_controlled=True)
        self.advance_time_and_run(1)

        # trough eject
        coil1.pulse.assert_called_once_with()
        assert not coil2.pulse.called

        self.machine.switch_controller.process_switch("s_ball_switch1", 0)
        self.advance_time_and_run(1)
        self.assertEquals(0, device1.balls)


        # launcher receives but waits for player to eject
        self.machine.switch_controller.process_switch("s_ball_switch_launcher", 1)
        self.advance_time_and_run(1)
        self.assertEquals(1, device2.balls)

        coil1.pulse.assert_called_once_with()
        assert not coil2.pulse.called

        # player shoots the ball
        self.machine.switch_controller.process_switch("s_launch", 1)
        self.advance_time_and_run(1)
        self.machine.switch_controller.process_switch("s_launch", 0)
        self.advance_time_and_run(1)

        coil1.pulse.assert_called_once_with()
        coil2.pulse.assert_called_once_with()
        coil1.pulse = MagicMock()
        coil2.pulse = MagicMock()


        self.machine.switch_controller.process_switch("s_ball_switch_launcher", 0)
        self.advance_time_and_run(1)
        self.assertEquals(0, device2.balls)

        self.advance_time_and_run(3)

        # too soft and it comes back
        self.machine.switch_controller.process_switch("s_ball_switch_launcher", 1)
        self.advance_time_and_run(3)
        self.assertEquals(1, device2.balls)

        # player drinks his coffee
        self.advance_time_and_run(300)

        assert not coil1.pulse.called
        assert not coil2.pulse.called

        # player shoots the ball again
        self.machine.switch_controller.process_switch("s_launch", 1)
        self.advance_time_and_run(1)
        self.machine.switch_controller.process_switch("s_launch", 0)
        self.advance_time_and_run(1)

        assert not coil1.pulse.called
        coil2.pulse.assert_called_once_with()

        self.machine.switch_controller.process_switch("s_ball_switch_launcher", 0)
        self.advance_time_and_run(1)
        self.assertEquals(0, device2.balls)

        assert not coil1.pulse.called
        coil2.pulse.assert_called_once_with()

        self.machine.switch_controller.process_switch("s_playfield", 1)
        self.advance_time_and_run(0.1)
        self.machine.switch_controller.process_switch("s_playfield", 0)
        self.advance_time_and_run(1)

        self.assertEquals(1, playfield.balls)

        self.assertEquals(0, self._captured)
        self.assertEquals(0, self._missing)

