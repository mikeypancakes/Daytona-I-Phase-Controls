from tt_engine.tt_dataclass import Module, Step, opcodeCommand
import numpy as np

class DaytonaBase:
    def get_tt_dictionary(self) -> dict[str, list[Step]]:
        modules = [
            self.TWAVE_Module_PathA,
            self.TWAVE_Module_PathB,
            self.TWAVE_Module_PathC,
            self.CONTROL_Module,
        ]
        return {
            m.name: sorted(m.steps, key=lambda s: (s.abs_time_ms, s.priority))
            for m in modules
        }

    def get_tts(self):
        tt_dict = self.get_tt_dictionary()
        cleaned_tt_dict = {}

        for module_name, steps in tt_dict.items():
            cleaned_tt_dict[module_name] = list(steps)

        return cleaned_tt_dict

class Daytona_HDC_tt(DaytonaBase):
    def __init__(self, intent=None):
        self.TWAVE_Module_PathA = Module("4")
        self.TWAVE_Module_PathB = Module("5")
        self.TWAVE_Module_PathC = Module("6")
        self.CONTROL_Module = Module("0")
        self.intent = intent

        #Timing Table Saugage Maker

        self.init_steps(abs_time_ms=0.0)
        self.fill(abs_time_ms=self.intent['release'])
        self.trap(abs_time_ms=self.intent['release'] + self.intent['fill'])
        self.release(abs_time_ms=0.0) #i know, its confusing, but we start with release
        self.stall(abs_time_ms=self.intent['sipPeriod'] - self.intent['stallDuration'])
        self.flush(SIP_period=self.intent['sipPeriod'])
        self.wait(SIP_period=self.intent['sipPeriod'])
        self.build_twrs(SIP_period=self.intent['sipPeriod'])

    def init_steps(self, abs_time_ms):
        '''
        Initial steps taken before timing table cycle begins.
        These steps are only called once during entirety of timing table.
        Priority is assigned to these values to ensure they occur first.
        '''
        #Init Path A
        self.TWAVE_Module_PathA.add_step("Path A Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']), 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        self.TWAVE_Module_PathA.add_step("Path A Gate.control", 
                                         0.0, #Close gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        self.TWAVE_Module_PathA.add_step("TW1_NO_OP",
                                         0.0, 
                                         opcodeCommand.WAIT, #WAIT_4_READY to start release sequence on receipt of sync pulse
                                         abs_time_ms, priority=-1)
        #Init Path B
        self.TWAVE_Module_PathB.add_step("Path B Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']),
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        #Init OBA+Path C
        self.TWAVE_Module_PathC.add_step("Path C Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']), 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        self.TWAVE_Module_PathC.add_step("TW3_NO_OP",
                                     0.0, 
                                     opcodeCommand.WAIT, #WAIT_4_SYNC to delay the opening of fill gate
                                     abs_time_ms)
        #Init Control Board
        self.CONTROL_Module.add_step("Digitizer Gate.DIO",
                                     0.0, 
                                     opcodeCommand.WRITE, #Digitizer gate low.
                                     abs_time_ms, priority=-1)
        self.CONTROL_Module.add_step("CB_NO_OP",
                                     0.0, 
                                     opcodeCommand.WAIT, #WAIT_4_SYNC
                                     abs_time_ms)
         
    def fill(self, abs_time_ms):
        '''
        Fill sequence for Path A and Path B. It assumes the timing table cycle begins on a release.
        Therefore, absolute time in ms is defined as abs_time_ms = release time

        Second fill is offset from the intitial release by the fill time + trap time + release time.

        Entrance travelling wave is static in Daytona and must be set via the method.
        '''
        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set FWD to begin fill
                                         1.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms) #Begin fill after release at start of loop
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.amplitude", #Set OBA fill amplitude
                                        self.intent['fillAmp'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms) 
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.frequency", #Set OBA fill frequency                 
                                        self.intent['fillFrequency'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("Fill Gate.control", #Open fill gate
                                         1.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        
        offset_second_fill = self.intent['fill'] + self.intent['trap'] + self.intent['release'] #offset the start of the second fill by trap + release

        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set FWD to begin second fill
                                         1.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + offset_second_fill)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.amplitude", #Set OBA fill amplitude
                                        self.intent['fillAmp'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms = abs_time_ms + offset_second_fill)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.frequency", #Set OBA fill frequency                 
                                        self.intent['fillFrequency'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms = abs_time_ms + offset_second_fill)
        self.TWAVE_Module_PathC.add_step("Fill Gate.control", #Open fill gate
                                         1.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + offset_second_fill)
        
    def trap(self, abs_time_ms):
        '''
        Trap sequence for Path A and Path B. The first trap in absolute time is defined as:
        abs_time_ms = release time + fill time

        Second trap is offset from the intitial release by the fill time + trap time + release time.
        '''
        #Path A Trap
        self.TWAVE_Module_PathC.add_step("Fill Gate.control", #Close fill gate, begin trap
                                        0.0, 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set REV to send ions to ICD
                                        0.0, 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.amplitude", #Close fill gate, begin trap
                                        self.intent['trapAmp'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.frequency", #Close fill gate, begin trap                 
                                        self.intent['trapFrequency'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        
        trap_offset = self.intent['release'] + self.intent['fill'] + self.intent['trap']  #offset the start of the trap on path B by the release + fill
        
        self.TWAVE_Module_PathC.add_step("Fill Gate.control", #Close fill gate, begin trap                     
                                         0.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + trap_offset)
        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set REV to send ions to ICD
                                         0.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + trap_offset)
        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set REV to send ions to ICD
                                         0.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + trap_offset)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.amplitude", #Close fill gate, begin trap
                                         self.intent['trapAmp'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + trap_offset)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.frequency", #Close fill gate, begin trap
                                         self.intent['trapFrequency'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms = abs_time_ms + trap_offset)

    def release(self, abs_time_ms):

        '''
        Release sequence for Path A and Path B. The first release in absolute time is defined as:
        abs_time_ms = 0. Release begins on receipt of sync pulse.
        
        Second release is offset from the intitial release by the fill time + trap time + release time (SIP period).
        '''
        #Path A Release
        self.TWAVE_Module_PathA.add_step("Path A Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']), #End flush
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.amplitude", #Close fill gate, begin trap
                                         self.intent['releaseAmp'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.frequency", #Close fill gate, begin trap
                                         self.intent['releaseFrequency'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.direction",
                                         1.0, #Set FWD to go down path A
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.TWAVE_Module_PathA.add_step("Path A Gate.control", 
                                         1.0, #Open gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
  
        #Path B Release
        offset_release = self.intent['sipPeriod'] #offset the release of path B by the SIP period

        self.TWAVE_Module_PathB.add_step("Path B Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']), #End flush
                                         opcodeCommand.WRITE, 
                                         abs_time_ms + offset_release)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.amplitude", #Close fill gate, begin trap
                                         self.intent['releaseAmp'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms + offset_release)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.frequency", #Close fill gate, begin trap
                                         self.intent['releaseFrequency'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms + offset_release)
        self.TWAVE_Module_PathC.add_step("On Board Accumulation Traveling Wave.direction",
                                         0.0, #Set REV to go down path B
                                         opcodeCommand.WRITE, 
                                         abs_time_ms + offset_release)
        self.TWAVE_Module_PathB.add_step("Path B Gate.control", 
                                         1.0, #Open gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms + offset_release)
        
    def stall(self, abs_time_ms):
        '''
        Stalling ions during ISD period. This stalling value is configurable and occurs midway through separation.
        The first stall is defined as abs_time_ms = SIP period - stall time. The stall on the second path is offset from the first by the SIP period/2 to stall ions in the middle of separation.
        '''

        #Path A Stall
        offset_stall = self.intent['sipPeriod'] + self.intent['stallDuration'] #offset the start of the stall

        self.TWAVE_Module_PathA.add_step("Path A Separation Traveling Wave.amplitude", 
                                         0.0, #Close gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        #Path B Stall
        self.TWAVE_Module_PathB.add_step("Path B Separation Traveling Wave.amplitude", 
                                         0.0, #Close gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms + offset_stall)

    def flush(self, SIP_period):
        '''
        Flush sequence for Path A and Path B.
        Path B flush occurs at abs_time_ms = SIP period - flush.
        Path A flush occurs at abs_time_ms = 2 * SIP period + stall time - flush.
        '''
        #Path B Flush
        self.TWAVE_Module_PathB.add_step("Path B Dynamic Guard.setpoint", 
                                         self.intent['flushVoltage'], 
                                         opcodeCommand.WRITE, 
                                         SIP_period - 5.0) #Flush 5 ms before end of SIP period
        #Path A Flush
        self.TWAVE_Module_PathA.add_step("Path A Dynamic Guard.setpoint", 
                                         self.intent['flushVoltage'], 
                                         opcodeCommand.WRITE, 
                                         2 * SIP_period + self.intent['stallDuration'] - 5.0) #Flush 5 ms before end of SIP period

    def wait(self, SIP_period):
        '''
        Wait step to ensure timing table cycle repeats after completion. This step is added at the end of the timing table and has a wait command that waits for the sync pulse to begin the next cycle.
        '''
        self.CONTROL_Module.add_step("CB_NO_OP",
                                     0.0, 
                                     opcodeCommand.WAIT, #WAIT_4_SYNC
                                     SIP_period - 5.0,
                                     priority=2) #Wait 5 ms before end of SIP period to ensure timing table cycle repeats after completion
        
        self.TWAVE_Module_PathA.add_step("TW1_NO_OP",
                                         0.0,
                                         opcodeCommand.WAIT, #WAIT_4_READY for path A stall.
                                         SIP_period - self.intent['stallDuration'],
                                         priority=2)
        
        self.TWAVE_Module_PathA.add_step("TW1_NO_OP",
                                         0.0,
                                         opcodeCommand.WAIT, #WAIT_4_READY for path A flush.
                                         SIP_period + (SIP_period - 5.0),
                                         priority=2)
        
        self.TWAVE_Module_PathB.add_step("TW2_NO_OP",                                        
                                         0.0,
                                         opcodeCommand.WAIT, #WAIT_4_READY for Path B Flush.
                                         SIP_period - 5.0,
                                         priority=2)
        
        self.TWAVE_Module_PathB.add_step("TW2_NO_OP",                                        
                                         0.0,
                                         opcodeCommand.WAIT, #WAIT_4_READY for Path B Flush.
                                         SIP_period + (SIP_period - self.intent['stallDuration']),
                                         priority=2)

        self.TWAVE_Module_PathC.add_step("TWC_NO_OP",                                        
                                         0.0,
                                         opcodeCommand.WAIT, #WAIT_4_READY for Path B Flush.
                                         self.intent['release'] + self.intent['fill'],
                                         priority=2)
        
        self.TWAVE_Module_PathC.add_step("TWC_NO_OP",                                        
                                         0.0,
                                         opcodeCommand.WAIT, #WAIT_4_READY for Path B Flush.
                                         self.intent['release'] + self.intent['fill'] + self.intent['trap'] 
                                         + self.intent['release'] + self.intent['fill'],
                                         priority=2)

    def build_twrs(self, SIP_period):
        twr_dict = {}
        twr_profiles = ['pathA_traveling_wave_profile', 'pathB_traveling_wave_profile']

        for key in twr_profiles:
            twr_dict[key] = {
                "ramp_profile": []
            }

            for ramp in self.intent[key]['ramps']:
                twr_dict[key]['ramp_profile'].append({
                    "time_ms": ramp['time'],
                    "frequency": ramp['state']['frequency'],
                    "amplitude": ramp['state']['amplitude'],
                })

        self.build_path_C_twr(pathA_pathB_twrs=twr_dict, SIP_period=SIP_period)

        return twr_dict
        
    def build_path_C_twr(self, pathA_pathB_twrs, SIP_period):
        for path, ramp_profile in pathA_pathB_twrs.items():
            times = np.array([freq_ramp['time_ms'] for freq_ramp in ramp_profile['ramp_profile']])
            freqs = np.array([freq_ramp['frequency'] for freq_ramp in ramp_profile['ramp_profile']])  
            amps = np.array([freq_ramp['amplitude'] for freq_ramp in ramp_profile['ramp_profile']])

            sip_freq = np.interp(SIP_period, times, freqs)

            print(times, freqs, sip_freq)       

class Daytona_SinglePath_tt(DaytonaBase):

    def __init__(self, intent=None):

        self.TWAVE_Module_PathA = Module("4")
        self.TWAVE_Module_PathB = Module("5")
        self.TWAVE_Module_PathC = Module("6")
        self.CONTROL_Module = Module("0")
        self.intent = intent
        self.flush_time = 5.0

        self.pathSelection_dict = {
            'Path A' : [self.TWAVE_Module_PathA, 'Path A Gate.control', 'Path A Dynamic Guard.setpoint'], #Gate mapping based on user path selection
            'Path B' : [self.TWAVE_Module_PathB, 'Path B Gate.control', 'Path A Dynamic Guard.setpoint']
        }

        #Timing Table Saugage Maker

        sep_dt, oba_dt = self.dead_time_calc()

        self.init_steps(abs_time_ms=0.0)
        self.fill(abs_time_ms=self.intent['release'] + oba_dt)
        self.trap(abs_time_ms=self.intent['release'] + self.intent['fill'] + oba_dt)
        self.release(abs_time_ms=0.0) #i know, its confusing, but we start with release
        #self.stall(abs_time_ms=self.intent['sipPeriod'] - self.intent['stallDuration']) I dont think were going to stall on single path...
        self.flush(abs_time_ms=self.intent['sipPeriod'] + sep_dt - self.flush_time)
        self.wait(abs_time_ms=self.intent['release'] + self.intent['fill'] + oba_dt + self.intent['trap'])
        #self.build_twrs(SIP_period=self.intent['sipPeriod']) Not ready yet.

    def init_steps(self, abs_time_ms):

        #Init Path A
        self.TWAVE_Module_PathA.add_step("Path A Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']), 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        self.TWAVE_Module_PathA.add_step("Path A Gate.control", 
                                         0.0, #Close gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        self.TWAVE_Module_PathA.add_step("TW1_NO_OP",
                                         0.0, 
                                         opcodeCommand.WAIT, #WAIT_4_READY to start release sequence on receipt of sync pulse
                                         abs_time_ms, priority=-1)

        #Init Path B
        self.TWAVE_Module_PathB.add_step("Path B Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']),
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        
        #Init OBA+Path C
        self.TWAVE_Module_PathC.add_step("Path C Dynamic Guard.setpoint", 
                                         abs(self.intent['flushVoltage']), 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms, priority=-1)
        
        self.TWAVE_Module_PathC.add_step("TW3_NO_OP",
                                     0.0, 
                                     opcodeCommand.WAIT, #WAIT_4_SYNC to delay the opening of fill gate
                                     abs_time_ms)
        
        #Init Control Board
        self.CONTROL_Module.add_step("Digitizer Gate.DIO",
                                     0.0, 
                                     opcodeCommand.WRITE, #Digitizer gate low.
                                     abs_time_ms, priority=-1)
        self.CONTROL_Module.add_step("CB_NO_OP",
                                     0.0, 
                                     opcodeCommand.WAIT, #WAIT_4_SYNC
                                     abs_time_ms)
    
    def fill(self, abs_time_ms):
        '''
        Fill sequence for SINGLE PATH ONLY. It assumes the timing table cycle begins on a release.
        Therefore, absolute time in ms is defined as abs_time_ms = release time + OBA dead time

        Entrance travelling wave is static in Daytona and must be set via the method.

        Only one path is used.
        '''

        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set FWD to begin fill
                                         1.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms) #Begin fill after release at start of loop
        self.TWAVE_Module_PathC.add_step("OBA Traveling Wave.amplitude", #Set OBA fill amplitude
                                        self.intent['fillAmp'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms) 
        self.TWAVE_Module_PathC.add_step("OBA Traveling Wave.frequency", #Set OBA fill frequency                 
                                        self.intent['fillFrequency'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("Fill Gate.control", #Open fill gate
                                         1.0, 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)

    def trap(self, abs_time_ms):
        '''
        Trap sequence for single path. The  trap in absolute time is defined as:
        abs_time_ms = release time + fill time + OBA dead time

        Second trap is offset from the intitial release by the fill time + trap time + release time.
        '''
        #Path A Trap
        self.TWAVE_Module_PathC.add_step("Fill Gate.control", #Close fill gate, begin trap
                                        0.0, 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("Waste Traveling Wave.direction", #Set REV to send ions to ICD
                                        0.0, 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("OBA Traveling Wave.amplitude", #Close fill gate, begin trap
                                        self.intent['trapAmp'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        self.TWAVE_Module_PathC.add_step("OBA Traveling Wave.frequency", #Close fill gate, begin trap                 
                                        self.intent['trapFrequency'], 
                                        opcodeCommand.WRITE, 
                                        abs_time_ms)
        
    def release(self, abs_time_ms):
        '''
        Release sequence for Path A and Path B. The first release in absolute time is defined as:
        abs_time_ms = 0. Release begins on receipt of sync pulse.
        '''

        self.pathSelection_dict[self.intent['HDCpath']][0].add_step(self.pathSelection_dict[self.intent['HDCpath']][2], 
                                         abs(self.intent['flushVoltage']), #End flush
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.pathSelection_dict[self.intent['HDCpath']][0].add_step("OBA Traveling Wave.amplitude", #Close fill gate, begin trap
                                         self.intent['releaseAmp'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.pathSelection_dict[self.intent['HDCpath']][0].add_step("OBA Traveling Wave.frequency", #Close fill gate, begin trap
                                         self.intent['releaseFrequency'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.pathSelection_dict[self.intent['HDCpath']][0].add_step("OBA Traveling Wave.direction",
                                         1.0 if self.intent['HDCpath'] == 'Path A' else 0.0, #Set FWD to go down path A
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        self.pathSelection_dict[self.intent['HDCpath']][0].add_step(self.pathSelection_dict[self.intent['HDCpath']][1], 
                                         1.0, #Open gate
                                         opcodeCommand.WRITE, 
                                         abs_time_ms)
        
    def flush(self, abs_time_ms):
        '''
        Flush sequence for Single Path and Path C.
        '''
        #Path Flush
        self.pathSelection_dict[self.intent['HDCpath']][0].add_step(self.pathSelection_dict[self.intent['HDCpath']][2], 
                                         self.intent['flushVoltage'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms) #Flush selected path
        #Path C Flush
        self.TWAVE_Module_PathC.add_step("Path C Dynamic Guard.setpoint", 
                                         self.intent['flushVoltage'], 
                                         opcodeCommand.WRITE, 
                                         abs_time_ms) #Flush Path C/exit too

    def wait(self, abs_time_ms):
        '''
        Wait_4_Ready step to occur prior to ion release at end of cycle.
        '''
        self.TWAVE_Module_PathC.add_step('TW3_NO_OP', 
                                    0.0, 
                                    opcodeCommand.WAIT, 
                                    abs_time_ms) #Wait for ready on path OBA

    def dead_time_calc(self):
        '''
        The ion mobiliy cycle time can be modeled as:
            Fill + Trap + Release + OBA_Dead_Time = Separation + Flush + Separation_Dead_Time.

        Either OBA_Dead_Time or Separation_Dead_Time will be non-zero based on the following equations:
            OBA_Dead_Time > 0 when Separation + Flush > Fill + Trap + Release
            Separation_Dead_Time > 0 when Fill + Trap + Release > Separation + Flush

        When dead time is non-zero the following is how they will be calculated:
            OBA_Dead_Time = Separation + Flush - (Fill + Trap + Release)
            Separation_Dead_Time = Fill + Trap + Release - (Separation + Flush)
        '''

        sep_dt = max(0, self.intent['fill'] + self.intent['trap'] + self.intent['release'] - (self.intent['sipPeriod'] + self.flush_time))
        oba_dt = max(0, self.intent['sipPeriod'] + self.flush_time - (self.intent['fill'] + self.intent['trap'] + self.intent['release']))
        
        return sep_dt, oba_dt
    