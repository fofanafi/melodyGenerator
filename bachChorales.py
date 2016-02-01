from music21 import *
import util
import model
import pickle
import random

MELODIES_FILE = "savedMelodies.p"
melodies = []
frozen_streams = []
BWVNumbers = [250, 251, 252, 253, 255, 260, 262, 263, 264, 267, \
              268, 271, 284, 287, 290, 292, 293, 294, \
              302, 303, 307, 308, 317, 318, 325, 329, 332, \
              336, 339, 340, 346, 347, 348, 355, 359, 360, 361, \
              365, 370, 371, 375, 376, 377, 378, 379, \
              380, 384, 385, 386, 387, 388, 389, 392, 393, 394, \
              395, 397, 398, 401, 402, 414, 415, 422, \
              426, 427, 428, 429, 430, 431, 432, 433, 436, 438]
threeFour = 0
fourFour = 0
twoTwo = 0
twoFour = 0

def getKey(stream):
    """
    Input: any music21 Stream (a Score, Part, Measure, etc.)
    Output: a tuple representing the key of the Stream
            For example, if the key is A minor, the return value 
            will be ('A', 'minor')
    """
    music21KeySignature = stream.flat.getElementsByClass(key.KeySignature)
    if len(music21KeySignature.elements) == 0:
        return None
    elif len(music21KeySignature.elements) >= 2:
        print "More than two keys detected.\n"
    pitchAndMode = music21KeySignature.elements[0].pitchAndMode
    return pitchAndMode

def getTimeSignature(stream):
    timeSignatures = stream.flat.getElementsByClass(meter.TimeSignature)
    if len(timeSignatures) != 1:
        return len(timeSignatures)
    return timeSignatures[0]

def getScaleDegree(pitchAndMode, note):
    """
    Given a note and a pitchAndMode, return the scale degree of the note.
    """
    pi = pitchAndMode[0]
    mode = pitchAndMode[1]
    ref_scale = None
    if pitchAndMode[1] == "major":
        ref_scale = scale.MajorScale(pi)
    else:
        ref_scale = scale.MinorScale(pi)
    degree = ref_scale.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note.name))
    return degree


def intervalToC(pitch):
    """
    Given a pitch, determine the minimum number of half steps to C.
    """
    interval = (60 - pitch.midi) % 12
    if interval >= 6:
        interval -= 12
    return interval

def transposeToC(stream):
    interval = intervalToC(pitch.Pitch(getKey(stream)[0].name + str(4)))
    rtn = stream.transpose(interval)
    rtn[1].keySignature = key.KeySignature(0)
    rtn[1].keySignature.mode = 'major'
    return rtn

def getFromCorpus(i):
    chorale = corpus.parse('bach/bwv' + str(i))
    melody = chorale.getElementById('Soprano')
    if melody != None:
        if getTimeSignature(melody).ratioString == "4/4" and getKey(melody)[1] == "major":
            melodies.append(melody)
            return
    melody = chorale.getElementById('S.')
    if melody != None:
        if getTimeSignature(melody).ratioString == "4/4" and getKey(melody)[1] == "major":
            melodies.append(melody)
            return
    melody = chorale.getElementsByClass(stream.Part)[0]
    if getTimeSignature(melody).ratioString == "4/4" and getKey(melody)[1] == "major":
        melodies.append(melody)
        return

def loadOneMelody():
    getFromCorpus(307)
    return melodies
        
def loadMelodies():
    for i in BWVNumbers:
        getFromCorpus(i)
    print "melodies loaded!...now transposing"
    for i in range (0, len(melodies)):
        melodies[i] = transposeToC(melodies[i])
    print "melodies transposed!"
    return melodies

def createPickle():
    loadMelodies()
    # melodies[i].show('musicxml')
    # messing with pickling
    for i in range(0, len(melodies)):
        curr_melody = melodies[i]
        sf = freezeThaw.StreamFreezer(curr_melody)
        data = sf.writeStr(fmt='pickle')
        frozen_streams.append(data)
    pickle.dump(frozen_streams, open(MELODIES_FILE, "wb"))
    
def getMelodiesFromPickle():
    thawed_streams = []
    data = pickle.load(open(MELODIES_FILE, "rb"))
    st = freezeThaw.StreamThawer()
    for frozen_stream in data:
        st.openStr(frozen_stream)
        s = st.stream
        thawed_streams.append(s)
    return thawed_streams
    
if __name__ == "__main__":
  createPickle()
