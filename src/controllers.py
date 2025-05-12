import math
import logging

from collections import deque
from enums.states import ControllerState

class PIControllerPump:
    def __init__(self, id: str, params: dict) -> None:
        self.id = id
        self.state = ControllerState.MANUAL
        # Control params
        self.q0 = float(params["control"]["q0"])
        self.q1 = float(params["control"]["q1"])
        # System delay
        self.tr  = int(params["time"]["delay_s"])
        # Default setpoint (m3/h) and manual operation point (%)
        self.r = float(params["default"]["sp"])
        self.manual_u = float(params["default"]["u"])
        # Last written values
        self.last_u: float = 0
        # Default settings
        self.hyst_top_offset = float(params["hysteresis"]["top_offset"])
        self.hyst_bottom_offset = float(params["hysteresis"]["bottom_offset"])
        self.sat_top_limit = float(params["saturation"]["top_limit"])
        self.sat_bottom_limit = float(params["saturation"]["bottom_limit"])
        self.aw_gain = float(params["anti_windup"]["gain"])
        # Default control values of u and e
        self.u = deque([0]*self.tr, maxlen=self.tr)
        self.e = deque([0]*self.tr, maxlen=self.tr)
        # Control integral acumulator
        self.ui: float = 0

    # If control value is out of hysteresis bounds, the compute will return true
    def compute(self, y: float) -> bool:
        if self.state is ControllerState.MANUAL:
            self.r = y
            self.e.append(0)
            self.u.append(self.manual_u)
            self.ui = 0
            return self.u[-1] > self.last_u + self.hyst_top_offset or self.u[-1] < self.last_u - self.hyst_bottom_offset
        self.e.append(self.r - y)
        u_unsat = self.u[-1] + self.q0 * self.e[-1] + self.q1 * self.e[-2] + self.ui
        # if self.state is ControllerState.MANUAL:
        #     u_unsat = self.manual_u
        u_sat = min(max(u_unsat, self.sat_bottom_limit), self.sat_top_limit)
        logging.debug(f"[{self.id}]\n\t\t\t u_unsat: {u_unsat:.2f}\n\t\t\t u_sat: {u_sat:.2f}\n\t\t\t e: {self.e[-1]:.2f}\n\t\t\t ui: {self.ui:.2f}")
        self.ui = self.aw_gain * (u_sat - u_unsat)
        # logging.debug(f"[{self.id}] ui update: {self.ui:.2f}")
        self.u.append(u_sat)
        return self.u[-1] > self.last_u + self.hyst_top_offset or self.u[-1] < self.last_u - self.hyst_bottom_offset

    def set_sp(self, sp: float) -> None:
        self.r = sp

    def set_manual(self, enable: bool = True) -> None:
        self.state = ControllerState.AUTO
        if enable:
            self.state = ControllerState.MANUAL
    
    def set_manual_op(self, op: float) -> None:
        self.manual_u = op
    
    def set_last_u(self, u: float) -> None:
        self.last_u = u
    
    def get_op(self) -> float:
        return self.u[-1]
    
    def get_sp(self) -> float:
        return self.r
    
    def get_u_deque(self) -> deque:
        return self.u
    
    def get_e_deque(self) -> deque:
        return self.e
    
    def is_manual(self) -> bool:
        return self.state == ControllerState.MANUAL
    
    def get_manual_op(self) -> float:
        return self.manual_u

class PIController:
    def __init__(self, Kp: float, Ti: float, Ts: float, saturation_bounds: list[float], anti_windup: bool = True) -> None:
        self.state = ControllerState.NOT_RUNNING
        self.U: float = 0
        self.Ui: float = 0
        # Get PI params
        self.Kp = Kp
        self.Ti = Ti
        self.Ts = Ts
        # Get actuator saturation boundaries
        self.sat_low, self.sat_up = sorted(saturation_bounds)
        # Anti-windup
        self.AW = 0
        if anti_windup:
            self.AW = 1/math.sqrt(self.Ti)

    def compute(self, r: float, y: float) -> float:
        e = r - y
        Up = self.Kp * e
        Ui += self.Kp * self.Ts / self.Ti * e
        self.U = Up + self.Ui
        # Actuator limit (saturation)
        U_sat = max(self.sat_low, min(self.sat_up, self.U))
        if U_sat == self.sat_up:
            self.state = ControllerState.RUNNING_SAT_UP
        elif U_sat == self.sat_low:
            self.state = ControllerState.RUNNING_SAT_LOW
        else:
            self.state = ControllerState.RUNNING_OK
        # Antiwindup
        self.Ui += self.AW * self.Ts * (U_sat - self.U)
        return self.U

    def getState(self) -> ControllerState:
        return self.state
    
    def getU(self) -> float:
        return self.U
