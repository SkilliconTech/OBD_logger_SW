"""Identifiers for modes that do not use PIDs: $05, $06, $08, $09."""
from models.pid_directory.schema import Entry

MODE_05 = (
    Entry("$01-$0A", "Legacy oxygen sensor TIDs",
          "Standardized TIDs covering voltage thresholds, switching times, "
          "voltage extrema, transition time, and sensor period."),
    Entry("Mfr.", "Manufacturer-specific TIDs",
          "Appendix C lists the manufacturer-specific ranges."),
)

MODE_06 = (
    Entry("OBDMID", "CAN OBDMIDs (standardized)",
          "$01-$10, $21-$24, $31-$3D, $41-$50, $61-$64, $71-$74, $81-$86, "
          "$90-$91, $98-$99, $A1-$B3."),
    Entry("$E1-$FF", "CAN OBDMIDs (manufacturer-defined)",
          "Manufacturer-defined OBDMIDs use $E1-$FF."),
    Entry("$01-$0C", "CAN monitor TIDs (standardized)",
          "Appendix E defines unit and scaling IDs."),
    Entry("$80-$FE", "CAN monitor TIDs (manufacturer-defined)",
          "Manufacturer-defined TIDs use $80-$FE."),
    Entry("Legacy", "Legacy Mode $06",
          "Uses ECU-defined TIDs and component IDs."),
)

MODE_08 = (
    Entry("00", "Supported tests", "Discovers which tests the ECU supports."),
    Entry("01", "EVAP leak test", "Requests an onboard EVAP leak test."),
    Entry("02", "DPF regeneration",
          "Requests diesel particulate filter regeneration."),
)

MODE_09 = (
    Entry("01", "VIN message count", "Number of messages for the vehicle identification number."),
    Entry("02", "Vehicle identification number (VIN)", "Returns the vehicle identification number."),
    Entry("03", "Calibration ID message count", "Number of messages for the calibration identifiers."),
    Entry("04", "Calibration IDs", "Returns the calibration identifiers."),
    Entry("05", "Calibration verification message count", "Number of messages for the calibration verification numbers."),
    Entry("06", "Calibration verification numbers", "Returns the calibration verification numbers (CVN)."),
    Entry("07", "Spark-ignition tracking message count", "Number of messages for in-use performance tracking data."),
    Entry("08", "Spark-ignition tracking", "Returns in-use performance tracking data (spark ignition)."),
    Entry("09", "ECU name message count", "Number of messages for the ECU name."),
    Entry("0A", "ECU name", "Returns the ECU name."),
    Entry("0B", "Compression-ignition tracking", "Returns in-use performance tracking data (compression ignition)."),
    Entry("0C", "Engine serial number message count", "Number of messages for the engine serial number."),
    Entry("0D", "Engine serial number", "Returns the engine serial number."),
    Entry("0E", "Regulation or type approval message count", "Number of messages for the regulation or type approval number."),
    Entry("0F", "Regulation or type approval number", "Returns the regulation or type approval number."),
    Entry("10", "WWH-OBD protocol identification", "Returns the WWH-OBD protocol identification."),
    Entry("11", "WWH-OBD regulation revision number", "Returns the WWH-OBD regulation revision number."),
)