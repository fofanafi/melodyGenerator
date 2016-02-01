import music21
import bachChorales
import popSongs
from model import *
import argparse

def main():
  parser = argparse.ArgumentParser(description='Generate melodies.')
  parser.add_argument('-t', '--test', action='store_true',
                    help='test model')
  parser.add_argument('-d', '--debug', action='store_true',
                    help='debug model')
  parser.add_argument('-m', '--model', default='one',
                    help='specify the model type, basic, one or numSteps as an integer N. Defaults to one')
  parser.add_argument('-c', '--corpus', default='bach',
                    help='specify the corpus, bach or pop. Defaults to bach')

  args = parser.parse_args()

  if args.model == 'basic':
    print "Model: Basic"
    modelCreator = BasicModelCreator()
  elif args.model == 'one':
    print "Model: One-step lookahead"
    modelCreator = ModelCreator()
  else:
    print "Model: N-step"
    modelCreator = NStepModelCreator(numSteps = int(args.model))

  print "Loading corpus..."
  if args.corpus == 'bach':
    print "Corpus: Bach"
    corpus = bachChorales.getMelodiesFromPickle()
  else:
    print "Corpus: Pop"
    corpus = popSongs.loadCorpus()

  if args.debug:
    debugTest(modelCreator)
  elif args.test:
    fullTest(modelCreator, corpus)
  else:
    model = generateModel(modelCreator, corpus)
    generateSong(model)

def fullTest(modelCreator, corpus):
  print "Running cross validation..."
  tester = Tester(corpus, modelCreator)
  tester.runCrossValidation()

def debugTest(modelCreator):
  corpus = bachChorales.loadOneMelody()
  corpus[0].show()
  corpus = modelCreator.normalizeCorpus(corpus)

  tester = Tester(corpus, modelCreator)

  model = modelCreator.createModel(corpus)
  print model.dists
  print "(correct count, incorrect count, error)"
  print tester.testModel(model, corpus)

def generateSong(model, seed = 0):
  print "Generating song..."
  generator = Generator(model, seed)
  generator.setNextNote(Note.startOfSong)

  song = music21.stream.Stream()
  while True:
    nextNote = generator.generateNextNote()
    if nextNote == Note.endOfSong:
      break
    song.append(nextNote)
  # song.show('text')
  song.show('musicxml')

def generateModel(modelCreator, corpus):
  print "Creating model..."
  corpus = modelCreator.normalizeCorpus(corpus)
  model = modelCreator.createModel(corpus)
  return model

if __name__ == "__main__":
  main()
