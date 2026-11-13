from models.pid_directory.schema import ModeInfo

_NOTE_01_02 = (
    "Oxygen sensor slots follow the installed sensor layout. Appendix B maps each "
    "slot using PID $13 for one or two banks, or PID $1D for three or four banks.\n"
    "Support selectors ($00, $20, $40, $60, $80, $A0, $C0, $E0) return a bitmap of "
    "supported PIDs. They are read automatically and are not listed here."
)

MODE_INFO = {
    "01": ModeInfo("01", "Live powertrain data",
                   "Reads current emissions-related measurements and status.",
                   "PID", True),
    "02": ModeInfo("02", "Powertrain freeze frame",
                   "Reads stored data for the requested frame. PID $02 returns the "
                   "trigger DTC. Uses the applicable Mode $01 definitions and adds "
                   "a frame number.",
                   "PID", True),
    "03": ModeInfo("03", "Confirmed DTCs",
                   "Reads confirmed emissions-related fault codes.", "", False),
    "04": ModeInfo("04", "Clear diagnostic information",
                   "Clears emissions-related diagnostic data and resets readiness.",
                   "", False),
    "05": ModeInfo("05", "Oxygen sensor monitor results",
                   "Reads legacy oxygen sensor results by test ID and sensor selector.",
                   "TID", False),
    "06": ModeInfo("06", "Onboard monitor results",
                   "Reads monitor results and limits. Identifier structure depends "
                   "on protocol.",
                   "OBDMID / TID", False),
    "07": ModeInfo("07", "Pending DTCs",
                   "Reads emissions faults detected during the current or last "
                   "completed driving cycle.", "", False),
    "08": ModeInfo("08", "Onboard test control",
                   "Requests an onboard test or component operation by test ID.",
                   "TID", False),
    "09": ModeInfo("09", "Vehicle information",
                   "Reads vehicle identification, calibration, and performance data "
                   "by InfoType.",
                   "InfoType", True),
    "0A": ModeInfo("0A", "Permanent DTCs",
                   "Reads permanent emissions-related fault codes.", "", False),
}