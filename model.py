import util
import collections
import music21
import copy

class Note:
  startOfSong = music21.ElementWrapper('startOfSong')
  endOfSong = music21.ElementWrapper('endOfSong')

class Model:
  def __init__(self, dists):
    self.dists = dists

  def getNextNoteDistribution(self, state):
    """
    Returns a probability distribution for the next note,
    based on the current state (song so far) 
    """
    return self.dists[self.getEvidenceFromState(state)]

  def getEvidenceFromState(self, state):
    return state[-1]

  @staticmethod
  def toModelNote(note):
    modelNote = music21.note.Note(note.pitch.nameWithOctave)
    modelNote.quarterLength = note.quarterLength
    return modelNote

class BasicModel(Model):
  def getNextNoteDistribution(self, state):
    return self.dists

class NStepModel(Model):
  def __init__(self, dists, numSteps = 1):
    self.dists = dists
    self.numSteps = numSteps

  def getEvidenceFromState(self, state):
    return tuple(state[-self.numSteps:])

class ModelCreator:
  def __init__(self, modelCls = Model):
    self.modelCls = modelCls

  def createModel(self, corpus, laplace = 0):
    """
    Creates and returns a model, given a corpus.
    
    Assumes that each song in the corpus contains at least one note.
    """
    noteDists = collections.defaultdict(util.Counter)
    # Go through each song, adding to the count for P(next note|note)
    for song in corpus:
      previousNote = None
      for note in song:
        if previousNote is not None:
          noteDists[previousNote][note] += 1
        previousNote = note

    """
    for note in noteDists:
      # Apply Laplace smoothing
      noteDists[note].incrementAll(Note.allNotes(), laplace)
      # Normalize all the next note distributions
      noteDists[note].normalize()
    """

    model = self.modelCls(noteDists)
    return model

  def normalizeCorpus(self, corpus):
    # Make music21 notes work as keys of dictionaries
    music21.note.Note.__hash__ = lambda self: hash((self.pitch.nameWithOctave, self.duration.quarterLength))

    normalized = []
    for song in corpus:
      normalizedSong = music21.stream.Stream()
      normalizedSong.append(Note.startOfSong)

      song = song.flat.getElementsByClass(music21.note.Note)
      for note in song:
        normalizedSong.append(self.modelCls.toModelNote(note))
      
      normalizedSong.append(Note.endOfSong)
      normalized.append(normalizedSong) 
    return normalized

class BasicModelCreator(ModelCreator):
  def __init__(self, modelCls = BasicModel):
    self.modelCls = modelCls
  def createModel(self, corpus, laplace = 0):
    noteDist = util.Counter()
    for song in corpus:
      for note in song:
        if note != Note.startOfSong:
          noteDist[note] += 1

    model = self.modelCls(noteDist)
    return model

class NStepModelCreator(ModelCreator):
  def __init__(self, modelCls = NStepModel, numSteps = 1):
    self.modelCls = modelCls
    self.numSteps = numSteps

  def createModel(self, corpus, laplace = 0):
    """
    Creates and returns a model, given a corpus.
    
    Assumes that each song in the corpus contains at least one note.
    """
    noteDists = collections.defaultdict(util.Counter)
    # Go through each song, adding to the count for P(next note|note)
    for song in corpus:
      previousNotes = []
      for note in song:
        if len(previousNotes) > 0:
          noteDists[tuple(previousNotes)][note] += 1

        if len(previousNotes) == self.numSteps:
          previousNotes.pop(0)
        previousNotes.append(note)

    model = self.modelCls(noteDists, self.numSteps)
    return model

class Predictor:
  """
  Predicts the next note, based on previous notes.

  Usage:
  >>> predictor = Predictor(model)
  >>> while nextNote != Note.endOfSong:
  >>>   nextNote = predictor.predictAndSetNextNote()
  """

  def __init__(self, model):
    self.model = model
    self.state = []

  def setState(self, state):
    """
    Sets the state for the predictor (for example, all previous notes).
    """
    self.state = state

  def predictNextNote(self):
    """
    Predicts and returns the next note.
    """
    dist = self.getNextNoteDistribution()
    return dist.argMax()

  def getNextNoteDistribution(self):
    if not self.state:
      return self.getStartNoteDistribution()

    nextNoteDist = self.model.getNextNoteDistribution(self.state)
    return nextNoteDist

  def setNextNote(self, note):
    """
    Adds the next note to the state.
    """
    self.state.append(note)

  def predictAndSetNextNote(self):
    nextNote = self.predictNextNote()
    self.setNextNote(nextNote)
    return nextNote

  def getStartNoteDistribution(self):
    dist = util.Counter()
    dist[Note.startOfSong] = 1
    return dist

class Generator(Predictor):
  """
  Generates new notes from an underlying model.
  """
  def __init__(self, model, seed = None):
    self.model = model
    self.state = []
    self.seed = seed

  def predictNextNote(self):
    dist = self.getNextNoteDistribution()
    return util.sample(dist, seed = self.seed)

  def generateNextNote(self):
    note = self.predictAndSetNextNote()
    if note == Note.endOfSong or note == Note.startOfSong:
      return note
    else:
      return copy.deepcopy(note)


class Tester():
  def __init__(self, corpus, modelCreator):
    self.modelCreator = modelCreator
    self.corpus = modelCreator.normalizeCorpus(corpus)

  def runCrossValidation(self, numFolds = 10):
    cum_train_error = 0.0
    cum_test_error = 0.0
    if len(self.corpus) < numFolds:
      numFolds = len(self.corpus)
    for i in range(numFolds):
      (train, test) = self.splitTrainAndTestSets(i, numFolds)
      model = self.modelCreator.createModel(train, laplace = 0)
      train_error = self.getTrainError(model, train)
      test_error = self.testModel(model, test)[2]
      print i, "Training error:", train_error, "Test error:", test_error
      cum_train_error += train_error
      cum_test_error += test_error
      
    avg_train_error = cum_train_error / numFolds
    avg_test_error = cum_test_error / numFolds
    print "Avg training error:", avg_train_error
    print "Avg testing error:", avg_test_error

  # TODO: Could make this faster by taking error as 1 - max(P(next note|note)) * P(note)?
  def getTrainError(self, model, trainSet):
    return self.testModel(model, trainSet)[2]

  def testModel(self, model, testSet, predictorCls = Predictor):
    """
    Tests the model on the testSet.

    Returns the correct_count, incorrect_count, and error.

    Assumes every song has a first note.
    """
    predictor = predictorCls(model)
    correct_count = 0
    incorrect_count = 0
    for song in testSet:
      for actual_next_note in song:
        predicted_next_note = predictor.predictNextNote()
        if actual_next_note == predicted_next_note:
          correct_count += 1
        else:
          incorrect_count += 1
        # print predicted_next_note, actual_next_note, incorrect_count
        predictor.setNextNote(actual_next_note)
    
    total_count = incorrect_count + correct_count
    error = incorrect_count / float(total_count)
    return correct_count, incorrect_count, error

  def splitTrainAndTestSets(self, n, numFolds = 10):
    """
    Splits the corpus into train and test sets by placing every nth
    song in the test set. n should be between 0 and numFolds-1, inclusive.
    """
    train = []
    test = []
    if len(self.corpus) < numFolds:
      numFolds = len(self.corpus)
    for i in range(len(self.corpus)):
      if i % numFolds == n:
        test.append(self.corpus[i])
      else:
        train.append(self.corpus[i])
    return train, test
