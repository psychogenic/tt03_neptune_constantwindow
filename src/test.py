import math
import cocotb
import os 

from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

displayNotes = {
            'NA':     0b00000010, # -
            'A':      0b11101110, # A
            'B':      0b00111110, # b
            'C':      0b10011100, # C
            'D':      0b01111010, # d
            'E':      0b10011110, # E
            'F':      0b10001110, # F
            'G':      0b11110110, # g
            }
            
displayProx = {
            'lowfar':       0b00111000,
            'lowclose':     0b00101010,
            'exact':        0b00000001,
            'hiclose':      0b01000110,
            'hifar':        0b11000100

}

os.environ['COCOTB_RESOLVE_X'] = 'RANDOM'
async def reset(dut):
    dut._log.info("reset")
    dut.rst.value = 1
    await ClockCycles(dut.clk, 20)
    dut.rst.value = 0
    dut.clk_config.value = 0 # 1khz clock
    await ClockCycles(dut.clk, 500)
    
    
async def startup(dut):
    clock = Clock(dut.clk, 1, units="ms")
    cocotb.start_soon(clock.start())
    await reset(dut)
            
async def getDisplayValues(dut):
    displayedValues = [None, None]
    attemptCount = 0
    while None in displayedValues or attemptCount < 3:
        displayedValues[int(dut.prox_select.value)] = int(dut.segments.value & 0x7F)
        
        await ClockCycles(dut.clk, 1)
        
        attemptCount += 1
        if attemptCount > 100:
            dut._log.error(f"NEVER HAVE {displayedValues}")
            return displayedValues
            
    dut._log.info(f'Display Segments: {displayedValues} ( [ {bin(displayedValues[0])} , {bin(displayedValues[1])}])')
    return displayedValues
    
async def inputPulsesFor(dut, tunerInputFreqHz:int, inputTimeSecs=0.51, sysClkHz=1e3):
    numPulses = tunerInputFreqHz * inputTimeSecs 
    pulsePeriod = 1/tunerInputFreqHz
    pulseHalfCycleUs = round(1e6*pulsePeriod/2.0)
    
    displayedValues = [None, None]
        
    for _pidx in range(math.ceil(numPulses)):
        dut.input_pulse.value = 1
        await Timer(pulseHalfCycleUs, units='us')
        dut.input_pulse.value = 0
        await Timer(pulseHalfCycleUs, units='us')
        
    dispV = await getDisplayValues(dut)
    
    return dispV
    


async def setup_tuner(dut):
    dut._log.info("start")
    await startup(dut)
    

async def note_toggle(dut, freq, delta=0, msg=""):
    dut._log.info(msg)
    await startup(dut)
    dispValues = await inputPulsesFor(dut, freq + delta, 1.65)  
    return dispValues
    
    

async def note_e(dut, eFreq=330, delta=0, msg=""):
    
    dispValues = await note_toggle(dut, freq=eFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['E'] & 0x7F)
    return dispValues


async def note_g(dut, delta=0, msg=""):
    gFreq = 196
    
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['G'] & 0x7F)
    return dispValues
    
    
async def note_b(dut, delta=0, msg=""):
    gFreq = 247
    
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['B'] & 0x7F)
    return dispValues
    

    
@cocotb.test()
async def note_e_highfar(dut):
    dispValues = await note_e(dut, eFreq=330, delta=9, msg="E high/far")
    assert dispValues[0] == (displayProx['hifar'] & 0x7F) 



    
@cocotb.test()
async def note_e_highfar_duplicate(dut):
    dispValues = await note_e(dut, eFreq=330, delta=9, msg="E high/far")
    assert dispValues[0] == (displayProx['hifar'] & 0x7F) 

    
@cocotb.test()
async def note_e_lowclose(dut):
    dispValues = await note_e(dut, eFreq=83, delta=-6, msg="E low/close")
    assert dispValues[0] == (displayProx['lowclose'] & 0x7F) 
    
    

    
@cocotb.test()
async def note_e_exact(dut):
    dispValues = await note_e(dut, eFreq=330, delta=0, msg="E exact")
    assert dispValues[0] == (displayProx['exact'] & 0x7F) 


@cocotb.test()
async def note_e_exact_fatstring(dut):
    dispValues = await note_e(dut, eFreq=83, delta=0, msg="E fat exact")
    assert dispValues[0] == (displayProx['exact'] & 0x7F) 
    
    

@cocotb.test()
async def note_g_lowclose(dut):
    dispValues = await note_g(dut, delta=-4, msg="G low/close")
    assert dispValues[0] == (displayProx['lowclose'] & 0x7F) 
    
@cocotb.test()
async def note_g_highclose(dut):
    dispValues = await note_g(dut, delta=5, msg="High/close")
    assert dispValues[0] == (displayProx['hiclose'] & 0x7F) 
    



    
@cocotb.test()
async def note_g_lowfar(dut):
    dispValues = await note_g(dut, delta=-10, msg="G low/far")
    assert dispValues[0] == (displayProx['lowfar'] & 0x7F) 
    
    

@cocotb.test()
async def note_B_high(dut, delta=3):
    dispValues = await note_b(dut, delta=5, msg="B high/close")
    assert dispValues[0] == (displayProx['hiclose'] & 0x7F) 
    

# don't know how to get this to work yet...
async def FIXMEnote_B_exact(dut):
    dut._log.info("B exact")
    await startup(dut)
    
    
    bFreq = 247
    periodMs = math.ceil(1e3/bFreq)
    noteclock = Clock(dut.input_pulse, periodMs, units="ms")
    cocotb.start_soon(noteclock.start())
    
    await Timer(2000, units='ms')
    dispValues = await getDisplayValues(dut)
    
    assert dispValues[1] == (displayNotes['B'] & 0x7F)
    assert dispValues[0] == (displayProx['exact'] & 0x7F) 
    
    

