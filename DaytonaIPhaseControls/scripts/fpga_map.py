#
# Mobilion Acorn REST API services
# Copyright (c) 2020 MOBILion Systems Inc.
# ALL RIGHTS RESERVED
# Author: Harry Collins

# For each board there is a dictionary that you index with the
# parameter # to get the corresponding FPGA address offset
# structure is:
#   <parameter>: <fpga offset>  #  <parameter name> -> <fpga name>

from enum import IntEnum

class TwaveAddresses(IntEnum):
    """Common addresses used for TWAVE speed ramping"""
    TWAVE_RAMP_END_FREQUENCY = 0x0320
    TWAVE_RAMP_END_AMPLITUDE = 0x032c
    TWAVE_INITIAL_AMPLITUDE_ADDRESS = 0x0048
    TWAVE_INITIAL_FREQUENCY_ADDRESS = 0x0224

SC = {84: 0x0100,  # FPGA_PRS_627 -> PRS_627
      85: 0x0104,  # FPGA_PRS_925 -> PRS_925
      86: 0x0108,  # FPGA_PRS_226 -> PRS_226
      146: 0x0020,  # FPGA_PRS_627_LIMIT -> PRS_627_LIMIT
      147: 0x0024,  # FPGA_PRS_925_LIMIT -> PRS_925_LIMIT
      148: 0x0028,  # FPGA_PRS_226_LIMIT -> PRS_226_LIMIT
      149: 0x002c,  # FPGA_SMA_SW -> SMA_SW
      150: 0x0030,  # FPGA_GATE -> GATE
      1000: 0x0000  # NO_OPERATION
      }

IO = {83: 0x0100,  # FPGA_Amp1Read -> Amp1Read
      84: 0x0104,  # FPGA_Amp2Read -> Amp2Read
      85: 0x0108,  # FPGA_Amp3Read -> Amp3Read
      86: 0x010c,  # FPGA_Amp4Read -> Amp4Read
      87: 0x0110,  # FPGA_Amp5Read -> Amp5Read
      88: 0x0114,  # FPGA_Amp6Read -> Amp6Read
      89: 0x0118,  # FPGA_Amp7Read -> Amp7Read
      90: 0x011c,  # FPGA_Amp8Read -> Amp8Read
      91: 0x0120,  # FPGA_P600V_Vread -> P600V_Vread
      92: 0x0124,  # FPGA_P600V_Iread -> P600V_Iread
      93: 0x0128,  # FPGA_N600V_Vread -> N600V_Vread
      94: 0x012c,  # FPGA_N600V_Iread -> N600V_Iread
      95: 0x0130,  # FPGA_FCUP1_IntOut -> FCUP1_IntOut
      96: 0x0134,  # FPGA_FCUP2_IntOut -> FCUP2_IntOut
      97: 0x0138,  # FPGA_QTOFOffsetRead -> QTOFOffsetRead
      98: 0x013c,  # FPGA_Vmon24V -> Vmon24V
      99: 0x0140,  # FPGA_QTOFPolarity -> QTOFPolarity
      116: 0x0020,  # FPGA_Amp1Set -> Amp1Set
      117: 0x0024,  # FPGA_Amp2Set -> Amp2Set
      118: 0x0028,  # FPGA_Amp3Set -> Amp3Set
      119: 0x002c,  # FPGA_Amp4Set -> Amp4Set
      120: 0x0030,  # FPGA_Amp5Set -> Amp5Set
      121: 0x0034,  # FPGA_Amp6Set -> Amp6Set
      122: 0x0038,  # FPGA_Amp7Set -> Amp7Set
      123: 0x003c,  # FPGA_Amp8Set -> Amp8Set
      146: 0x0040,  # FPGA_P600V_VMin -> P600V_VMin
      147: 0x0044,  # FPGA_P600V_VMax -> P600V_VMax
      148: 0x0048,  # FPGA_P600V_IMax -> P600V_IMax
      149: 0x004c,  # FPGA_N600V_VMin -> N600V_VMin
      150: 0x0050,  # FPGA_N600V_VMax -> N600V_VMax
      151: 0x0054,  # FPGA_N600V_IMax -> N600V_IMax
      152: 0x0058,  # FPGA_AMP1_Vmin -> AMP1_Vmin
      153: 0x005c,  # FPGA_AMP1_Vmax -> AMP1_Vmax
      154: 0x0060,  # FPGA_AMP2_Vmin -> AMP2_Vmin
      155: 0x0064,  # FPGA_AMP2_Vmax -> AMP2_Vmax
      156: 0x0068,  # FPGA_AMP3_Vmin -> AMP3_Vmin
      157: 0x006c,  # FPGA_AMP3_Vmax -> AMP3_Vmax
      158: 0x0070,  # FPGA_AMP4_Vmin -> AMP4_Vmin
      159: 0x0074,  # FPGA_AMP4_Vmax -> AMP4_Vmax
      160: 0x0078,  # FPGA_AMP5_Vmin -> AMP5_Vmin
      161: 0x007c,  # FPGA_AMP5_Vmax -> AMP5_Vmax
      162: 0x0080,  # FPGA_AMP6_Vmin -> AMP6_Vmin
      163: 0x0084,  # FPGA_AMP6_Vmax -> AMP6_Vmax
      164: 0x0088,  # FPGA_AMP7_Vmin -> AMP7_Vmin
      165: 0x008c,  # FPGA_AMP7_Vmax -> AMP7_Vmax
      166: 0x0090,  # FPGA_AMP8_Vmin -> AMP8_Vmin
      167: 0x0094,  # FPGA_AMP8_Vmax -> AMP8_Vmax
      }

PC = {32: 0x010c,  # FPGA_TopRTD -> TopRTD
      33: 0x0110,  # FPGA_BottomRTD -> BottomRTD
      34: 0x0114,  # FPGA_TopRTD_Spare -> TopRTD_Spare
      35: 0x0118,  # FPGA_BottomRTD_Spare -> BottomRTD_Spare
      163: 0x0028,  # FPGA_Top_RTD_Max -> Top_RTD_Max
      164: 0x002c,  # FPGA_Top_RTD_Min -> Top_RTD_Min
      165: 0x0030,  # FPGA_Top_RTD_Max_Spare -> Top_RTD_Max_Spare
      166: 0x0034,  # FPGA_Top_RTD_Min_Spare -> Top_RTD_Min_Spare
      167: 0x0038,  # FPGA_Bottom_RTD_Max -> Bottom_RTD_Max
      168: 0x003c,  # FPGA_Bottom_RTD_Min -> Bottom_RTD_Min
      169: 0x0040,  # FPGA_Bottom_RTD_Max_Spare -> Bottom_RTD_Max_Spare
      170: 0x0044,  # FPGA_Bottom_RTD_Min_Spare -> Bottom_RTD_Min_Spare
      }

TW = {112: 0x0034,  # FPGA_DC_ADC_CHAN_SEL -> DC_ADC_CHAN_SEL
      114: 0x0054,  # FPGA_TWA_ADC_CHAN_SEL -> TWA_ADC_CHAN_SEL
      116: 0x0074,  # FPGA_TWB_ADC_CHAN_SEL -> TWB_ADC_CHAN_SEL
      118: 0x0094,  # FPGA_TWC_ADC_CHAN_SEL -> TWC_ADC_CHAN_SEL
      147: 0x0030,  # FPGA_HV_MUX_TWA -> HV_MUX_TWA (Long Path Gate)
      148: 0x0048,  # FPGA_TWA_DAC_VREF -> TWA_AMP
      149: 0x004c,  # FPGA_TWA_DAC_OFFS_DWN -> TWA_OFFS_DWN
      150: 0x0050,  # FPGA_TWA_DAC_OFFS_UP -> TWA_OFFS_UP
      151: 0x0068,  # FPGA_TWB_DAC_VREF -> TWB_AMP
      152: 0x006c,  # FPGA_TWB_DAC_OFFS_DWN -> TWB_OFFS_DWN
      153: 0x0070,  # FPGA_TWB_DAC_OFFS_UP -> TWB_OFFS_UP
      154: 0x0088,  # FPGA_TWC_DAC_VREF -> TWC_AMP
      155: 0x008c,  # FPGA_TWC_DAC_OFFS_DWN -> TWC_OFFS_DWN
      156: 0x0090,  # FPGA_TWC_DAC_OFFS_UP -> TWC_OFFS_UP
      181: 0x0020,  # FPGA_DC_DAC_0 -> DC_DAC_0
      182: 0x0024,  # FPGA_DC_DAC_1 -> DC_DAC_1
      183: 0x0028,  # FPGA_DC_DAC_2 -> DC_DAC_2
      184: 0x002c,  # FPGA_DC_DAC_3_Guard -> DC_DAC_3_GUARD

      188: 0x0040,  #HV_MUX_TWB -> FPGA_HV_MUX_TWB (Mike added this)

      189: 0x0044,  # HV_MUX_TWC ->FPGA_HV_MUX_TWC (Short Path Gate)
      249: 0x0220,  # FPGA_TWA_START_PH -> TWA_START_PH
      250: 0x0228,  # FPGA_TWA_DIR -> TWA_DIR
      251: 0x0250,  # FPGA_TWB_START_PH -> TWB_START_PH
      252: 0x0258,  # FPGA_TWB_DIR -> TWB_DIR
      253: 0x0280,  # FPGA_TWC_START_PH -> TWC_START_PH
      254: 0x0288,  # FPGA_TWC_DIR -> TWC_DIR

      # added per email from Gerard
      185: 0x0224,  # TWA frequency
      186: 0x0254,  # TWB frequency
      187: 0x0284,  # TWC frequency


      1000: 0x0000,  # NO_OPERATION

      # Following entries do NOT have a parameter mapping in 'external' space,
      # but kept in the same structure as the current design assumes all parameters
      # have such mappings. Note using values of 10000 and greater to make such parameters
      # clear.
      10000: TwaveAddresses.TWAVE_RAMP_END_FREQUENCY,  # FPGA_TWA_RAMP_FREQ -> TWA_RAMP_FREQ
      11000: TwaveAddresses.TWAVE_RAMP_END_AMPLITUDE,  # FPGA_TWA_RAMP_AMP -> TWA_RAMP_AMP
      }
