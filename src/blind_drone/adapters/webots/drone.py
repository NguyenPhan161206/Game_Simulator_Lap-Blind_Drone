"""Camera-free device adapter. No Supervisor or full-world configuration access."""
import json
from math import isfinite

from blind_drone.contracts.runtime import MotionCommand, VehicleState
from blind_drone.control.manual import keyboard_command
from blind_drone.control.stabilizer import Stabilizer


def main():
    from controller import Robot

    robot = Robot()
    config = json.loads(robot.getCustomData())
    step_ms = int(robot.getBasicTimeStep())
    dt = step_ms / 1000.0
    gps, imu, gyro = (robot.getDevice(name) for name in ("gps", "imu", "gyro"))
    for device in (gps, imu, gyro):
        device.enable(step_ms)
    ranges = {name: robot.getDevice(name) for name in config["sensor_names"]}
    for device in ranges.values():
        device.enable(config["sensor_period_ms"])
    receiver, emitter = (robot.getDevice(name) for name in ("operator", "telemetry"))
    receiver.enable(step_ms)
    keyboard = robot.getKeyboard()
    keyboard.enable(step_ms)
    motors = [robot.getDevice(f"motor_{index}") for index in range(4)]
    for motor in motors:
        motor.setPosition(float("inf"))
        motor.setVelocity(0)
    stabilizer = Stabilizer(config)
    previous_position = None
    filtered_velocity = [0.0, 0.0, 0.0]
    previous_keys = set()
    remote = MotionCommand()
    remote_until = -1.0
    range_packet = None
    next_range_time = config["sensor_period_ms"] / 1000.0
    device_names = [robot.getDeviceByIndex(index).getName() for index in range(robot.getNumberOfDevices())]
    print("BLIND_DRONE_READY: W/S forward/back, A/D left/right, T/G up/down, Q/E yaw, SPACE brake, R reset", flush=True)
    while robot.step(step_ms) != -1:
        now = robot.getTime()
        while receiver.getQueueLength():
            try:
                packet = json.loads(receiver.getString())
                if packet == {"kind": "reset"}:
                    stabilizer.reset()
                    previous_position = None
                    filtered_velocity = [0.0, 0.0, 0.0]
                    remote, remote_until = MotionCommand(), -1.0
                    range_packet = None
                    next_range_time = now + config["sensor_period_ms"] / 1000.0
                else:
                    remote = MotionCommand.from_operator(packet, config["vehicle"])
                    remote_until = now + 0.25
            except (ValueError, TypeError, KeyError) as error:
                print("REJECTED_OPERATOR_PACKET:", str(error), flush=True)
            finally:
                receiver.nextPacket()
        keys = set()
        key = keyboard.getKey()
        while key != -1:
            keys.add(key & 0xFFFF)
            key = keyboard.getKey()
        if ord("R") in keys and ord("R") not in previous_keys:
            emitter.send(json.dumps({"kind": "reset_request"}).encode())
        previous_keys = keys
        command = remote if now < remote_until else keyboard_command(keys, config["vehicle"])
        position = tuple(gps.getValues())
        attitude = tuple(imu.getRollPitchYaw())
        angular_velocity = tuple(gyro.getValues())
        if not all(isfinite(value) for value in (*position, *attitude, *angular_velocity)):
            continue
        if previous_position is not None:
            raw_velocity = [(a - b) / dt for a, b in zip(position, previous_position)]
            filtered_velocity = [0.35 * a + 0.65 * b for a, b in zip(raw_velocity, filtered_velocity)]
        previous_position = position
        state = VehicleState(now, position, tuple(filtered_velocity), attitude, angular_velocity)
        speeds = stabilizer.step(state, command, dt)
        for motor, speed in zip(motors, speeds):
            motor.setVelocity(speed)
        if now + 1e-8 >= next_range_time:
            readings = {}
            for name, device in ranges.items():
                value = float(device.getValue())
                valid = isfinite(value) and 0 <= value <= config["sensors"]["range_max_m"] + 1e-6
                readings[name] = {
                    "distance_m": value if valid else None,
                    "valid": valid,
                    "at_limit": valid and value >= config["sensors"]["range_max_m"] - 1e-6,
                }
            range_packet = {"sample_time_s": now, "frame": "body_FLU", "readings": readings}
            next_range_time = now + config["sensor_period_ms"] / 1000.0
        telemetry = {
            "kind": "telemetry", "time_s": now,
            "position_m": position, "velocity_m_s": filtered_velocity,
            "attitude_rad": attitude, "angular_velocity_rad_s": angular_velocity,
            "ranges": range_packet, "motor_rad_s": speeds,
            "devices": device_names,
            "sources": {"position": "ideal_Webots_GPS", "attitude": "ideal_Webots_InertialUnit", "rates": "ideal_Webots_Gyro"},
        }
        emitter.send(json.dumps(telemetry, allow_nan=False, separators=(",", ":")).encode())


if __name__ == "__main__":
    main()
