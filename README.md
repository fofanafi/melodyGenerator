# melodyGenerator

This program generates new melodies by 'listening' to existing ones, using simple markov models.  The melodies can be viewed by any program that handles MusicXML files (e.g. Finale Reader, MuseScore).  It uses the music21 toolkit (http://web.mit.edu/music21).

## Classes and Code Overview

<tt>melodyGenerator.py</tt> -- The main script.

<tt>model.py</tt> -- Contains all classes used for machine learning. <br />
*Model*: Knows the probability distribution for the next note. <br />
*ModelCreator*: Creates a new model from a corpus. <br />
*Predictor*: Predicts the most probable next note. <br />
*Generator*: Samples from the probability distribution to generate the next note. <br />
*Tester*: Tests the accuracy of the model on the data set, using k-fold cross validation.

<tt>bachChorales.py</tt> -- Reads in Bach chorales from the music21 corpus. <br />
<tt>popSongs.py</tt> -- Reads in pop melodies (data set not included).

## Usage

To generate a new song: 	`python melodyGenerator.py` <br />
For help: 			`python melodyGenerator.py -h`
