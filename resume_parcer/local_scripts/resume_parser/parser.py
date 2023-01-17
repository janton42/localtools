#!/usr/bin/python3
import os
import joblib
import random
import json
import nltk
import warnings
import string

import pandas as pd

from datetime import datetime, time
from time import sleep
from django.conf import settings
from pathlib import Path
from pdfminer.high_level import extract_text
from striprtf.striprtf import rtf_to_text
from nltk.parse.corenlp import CoreNLPServer, CoreNLPParser

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

from .cleaner import create_features
from .messages import messages

class ResumeParser(object):
	"""Parses a user-input resume.

	Retrieves an uploaded resume file, checks the file type, converts the info
	to text; applies machine learning models, Stanford's Named Entity
	Recognition (NER) tagger, and other homegrown algorithms to label the
	parts of the resume for further processing.

	Attributes:
		birth: Timestamp of when an instance is created.
		name: The user name associated with the instance.
		server: A CoreNLPServer instance needed for the NER tagger.
		server.corenlp_options: A list of flags (strings) to be passed
			in the Java command when starting the server. Include
			'-preload', then list modules to load. This process only
			requires 'ner', but others can be added.
			['-preload','ner']
		server.java_options: A list of flags (strings) for Java.
		server.url = A string containing the url for a user interface
			with the tagger.
		bullet_feature_headings: List of heading names needed for the
			machine learning model. Must match the headings used when
			training the model.
		name_feature_headings: Same as 'bullet_feature_headings', but
			for the 'name' label.
		org_feature_headings: Same as 'bullet_feature_headings', but
			for the 'org' label.
		keepers: List of single-word tags from NER tagging.
		resume_out_path: String with the destination for user-specific
			output. The path is derived from the that in settings.py
			and should be in /static/username/
		resume_in_path: String with path to an uploaded file, which will
			be in the applicaiton's /uploads/ directory.
		resume_file_ext: String with the file type of the resume file.
		death: Timestamp of when the parser returns the final output.

	"""

	def __init__(self, name: str):
		super(ResumeParser, self).__init__()
		'''Inits ResumeParser with birth, name, server,
			server.corenlp_options, server.java_options, server.url,
			bullet_feature_headings, name_feature_headings,
			org_feature_headings, and keepers.

		Args:
			name: String of the username for the user requesting a
				parsed resume.
		 '''
		print('La Maquina lives!!!\t(ResumeParser instantiated.)')
		self.birth = datetime.now()
		self.name = str(name)
		self.server = CoreNLPServer()
		self.server.corenlp_options = ['-preload', 'ner']
		self.server.java_options = ['-mx5g']
		self.server.url = 'http://localhost:9000'
		self.bullet_feature_headings = [
			'stopword_%',
			'word_count',
			'proper_noun_%',
			'verb_%'
		]
		self.name_feature_headings = [
			'line_length',
			'word_count',
			'verb_%',
			'adj_%',
			'stopword_%',
			'punctuation_%',
			'number_%',
			'proper_noun_%',
			'symbol_count',
			'list_markers_count',
			'determiners_count',
			'name_count',
			'line_length_trans',
			'word_count_trans',
			'verb_%_trans',
			'adj_%_trans',
			'stopword_%_trans',
			'punctuation_%_trans',
			'number_%_trans',
			'proper_noun_%_trans'
		]
		self.org_feature_headings = [
			'line_length',
			 'word_count',
			 'verb_%',
			 'adj_%',
			 'stopword_%',
			 'punctuation_%',
			 'number_%',
			 'proper_noun_%',
			 'symbol_count',
			 'list_markers_count',
			 'determiners_count',
			 'name_count',
			 'company_count',
			 'line_length_trans',
			 'word_count_trans',
			 'verb_%_trans',
			 'adj_%_trans',
			 'stopword_%_trans',
			 'punctuation_%_trans',
			 'number_%_trans',
			 'proper_noun_%_trans'
		]
		self.keepers = keepers = [
					    'Name',
					    'Organization',
					    'Date',
					    'Email',
					    'City',
					    'Location',
					    'Number',
					    'Person',
					    'Bullet',
					    'State_or_province',
					    'Title',
					    'Nationality',
					    'None',
					    'Country',
					    'Url',
					    'Misc',
					]

	def get_resume_paths(self, resume_file: str):
		'''Retrieves relevant filepaths for handling input and output
		files.

		Args:
			resume_file: String with filename of uploaded file.

		Returns:
			Sets the resume_out_path, resume_in_path, and
			resume_file_ext attributes.

		'''
		self.resume_out_path = os.path.join(settings.RESUME_OUT_PATH,\
		 self.name + '/')

		os.makedirs(self.resume_out_path, exist_ok=True)
		self.resume_in_path = os.path.join(settings.BASE_DIR, resume_file)
		self.resume_file_ext = self.resume_in_path.split('.')[-1]

	def introduce_self(self):
		'''Prints basic information about the class to stdout.'''
		print('***INFORMATION***\n\
		Hi. I\'m a parser.\n\
		My name is {}.\n\
		I was born at {}\
		Here are my paths: \n\
		\tresume_in_path = "{}"\n\
		\tresume_out_path = "{}"\n\
		My resume file type is: {}'.format(\
		self.name,\
		self.birth,\
		self.resume_in_path,\
		self.resume_out_path,\
		self.resume_file_ext))

	def text_compiler(self):
		'''Pulls text from different types of files.

		Runs the proper text extraction function for the given file
		extension, which is the resume_file_ext attribute.

		Returns:
			A text and a csv file containing the text extracted from the
			input file. The files are saved in the user's output folder at
			/static/output/username/

		'''
		if self.resume_file_ext == 'pdf':
			text = extract_text(self.resume_in_path)
		elif self.resume_file_ext == 'rtf':
			with open(self.resume_in_path, 'r') as file:
				content = file.read()
				text = rtf_to_text(content)
		elif self.resume_file_ext == 'txt':
			with open(self.resume_in_path, 'r') as file:
				text = file.read()
		#TODO: other file types (docx, odx, etc)
		# print(text)
		# Write resume out as a plain text doc, regardless of input type,
		# with a standardized name.
		resume_text_filename = self.resume_out_path + self.name + '_resume.txt'
		with open(resume_text_filename, 'w') as f:
			f.write(text)

		df = pd.read_table(
			resume_text_filename,
			header=None,
			on_bad_lines='skip',
			skip_blank_lines=True,
			lineterminator='\n'
			)
		raw_filename = self.resume_out_path + self.name + '_out.csv'
		df.to_csv(raw_filename, header=['line'])

	def clean_text(self):
		'''Removes unnamed column from csv.

		Returns:
			Pandas DataFrame.
		'''

		# TODO(janton42): update this for general use
		filename = self.resume_out_path + self.name + '_out.csv'
		df = pd.read_csv(filename)
		df.drop('Unnamed: 0',axis=1, inplace=True)
		return df

	def classify_text(self, text):
		'''Homegrown ML models for classifying parts of a resume.

		Classifies 'bullets', 'names', and 'orgs' using machine learning
		models.

		Args:
			text: Pandas DataFrame with rows of unlabeled, raw text from
				an uploaded resume file.

		Returns:
			A Pandas DataFrame with each line labeled as either a name,
			organization, bullet statement, or none of those using 1's
			and 0's for labels.

			Also write's out the feature data into a csv in the user's
			output folder: /static/output/username/
		'''


	    # Build paths to the ML models
		bullet_model_path = os.path.join(settings.ML_MODELS_PATH, 'bullets.pkl')
		name_model_path = os.path.join(settings.ML_MODELS_PATH, 'names.pkl')
		org_model_path = os.path.join(settings.ML_MODELS_PATH, 'org.pkl')

		# Import the model that has already been trained and tested
		bullet_model = joblib.load(bullet_model_path)
		name_model = joblib.load(name_model_path)
		org_model = joblib.load(org_model_path)

		# Group numerical features by removing categorical ones
		cat_feat = ['line','line_nostop','line_stemmed','tagged_line']
		numeric_only = text.drop(cat_feat, axis=1)
		numeric_path = self.resume_out_path + self.name + '_numeric_only.csv'
		numeric_only.to_csv(numeric_path)

		# Get set of features used for the bullet_model. This MUST MATCH
		# the headers passed to the model during training.

		bullet_features = numeric_only[self.bullet_feature_headings]

		# Get set of name features
		name_features = numeric_only[self.name_feature_headings]

		# Get set of company features
		org_features = numeric_only[self.org_feature_headings]

		# Classify each line of the text as either bullet or not
		print('Reading resume...')
		bullet_classification = bullet_model.predict(bullet_features)
		name_classification = name_model.predict(name_features)
		org_classification = org_model.predict(org_features)

		# Add classification in binary (0,1) to main DataFrame
		text['is_bullet'] = bullet_classification
		text['is_name'] = name_classification
		text['is_org'] = org_classification

		# Return only the original line and the results of the automated
		# classification
		classified = text[[
		    'line',
		    'is_bullet',
		    'is_name',
		    'is_org'
		    ]]

		return classified

	def labeler(self, row):
		'''Labels named entities.

		Gives final labels using Stanford's NLP Named Entity tagger to
		supplement already tagged data. Fills in the non-bullet items,
		giving the "None" label to anything remaining unidentified.

		Args:
			row: A Pandas DataFrame

		Returns:
			Either a one-word string label, or a list of tuples
			containing individual words and their respective ner tags.
			For example:
			'Bullet'
			- or -
			[('word', 'TAG'),...]
		'''


		if row['is_bullet'] == 1:
			return 'Bullet'
		elif row['is_name'] == 1:
			return 'Name'
		else:
			if len(row['line']) == 1:
				return 'None'
			else:
				ents = self.ner_tagger.tag(row['line'].split())
				return ents

	def count_named_ents(self, label: str)-> int:
		'''Sums the named entities in a row.

		Takes in the list of tuples from 'label' column of a Pandas
		DataFrame, and sums the total number of NER tags that are
		not the general-purpose 'O' tag.

		Args:
			label: String or list of tuples.

		Returns:
			Integer sum of the named entities in a given row.

		'''


		skips = ['Name', 'Bullet', 'None']
		if label not in skips:
			count = sum([1 for pair in label if pair[1] != 'O'])
			return count
		else:
			return 0

	def relabeler(self, row):
		'''Applies a label to a row based on number of named entities.

		Looks at the total number of named entities in a row, and applies
		a single label as a string wherever possible.

		Returns:
			String or list of tuples. If there are multiple named entities
			further processin is needed to parse them, so relabeler
			returns the list of tuples untouched in such cases.
		'''
		if row['ents'] == 0 and row['label'] == 'Bullet'\
		 or row['label'] == 'Name':
			return row['label']
		elif row['ents'] == 1:
			label = [ent[1].capitalize() for ent in row['label'] if ent[1] != 'O']
			if label[0] != '':
				return label[0]
		elif row['ents'] == 0 and row['is_bullet'] == 0:
			return 'None'
		else:
			tags = list()
			for tag in row['label']:
				if tag[1] != 'O' and tag[1] not in tags:
					tags.append(tag[1])
			if len(tags) == 1:
				return tags[0].capitalize()
			else:
				return row['label']

	def tag_grouper(self, label:list)-> dict:
		'''Groups words together by their common tag.

		Takes in a list of word-tag tuples, and groups the words in the
		list by tag.

		Args:
			label: list of tuples containing word and tag pairs in the
				following format:
					[(word, TAG), ...]
		Returns:
			List of dictionaries. Each dictionary represents a grouping
			of words that have a common label and were in the same line
			of the original document.The list contains the tag, a list,
			and a single string containing the words associated with
			that tag. For example:
				[	{
						'label': 'Example',
						'words': ['Words', 'Associated', 'With', 'Label'],
						'phrase': 'Words Associated With Label'
					},
					{
						'label': 'Title',
						'words': ['Program', 'Manager'],
						'phrase': 'Program Manager'
					},
					...]
		'''
		locations = [
	        'City',
	        'STATE_OR_COUNTRY',
	        'Country'
	    ]
		utags = list()
		groups = list()
		for x in label:
			try:
				tag = x[1]
			except IndexError as e:
				print(e)
				tag = 'O'
				pass
			if tag not in utags:
				utags.append(tag)
		for tag in utags:
			group = {
	            'label': tag,
	            'words': list()
	        }
			for x in label:
				word = x[0].strip()
				tag = x[1]
				if tag == group['label'] and word not in group['words']:
					if tag != 'Date' and tag != 'Number':
						word = word.capitalize()
					if word not in string.punctuation:
						group['words'].append(word)
			group['phrase'] = ' '.join(group['words'])
			group['label'] = group['label'].capitalize()
			if group['label'] == 'O':
				group['label'] = 'None'
			elif group['label'] == 'Nationality':
				group['label'] = 'Language (human)'
			groups.append(group)
		return groups

	def get_loosies(self, row):
		'''Compiles grouped words into a Pandas DataFrame

		Gathers dictionaries from the 'grouped' column, and adds them to
		a Pandas DataFrame.

		Args:
			row: Pandas DataFrame.

		Returns:
			A new Pandas DataFrame with 'doc_line' matching the original
			'doc_line','line' matching the dictionary 'phrase',
			'label' matching the dictionary 'label', and all other \
			values set to zero (0.0).
		'''
		looks = 0
		detailed = pd.DataFrame(
	        {
	            'doc_line': [],
	            'line':[],
	            'is_bullet':[],
	            'is_name':[],
	            'is_org':[],
	            'label':[],
	            'ents':[]
	        }
	    )
		for dict_list in row.grouped:
			dl = row.iloc[[looks]]['doc_line']
			dl = dl[looks]
			looks += 1
			for phrase in dict_list:
				line = phrase['phrase']
				label = phrase['label']
				detail_1 = pd.DataFrame(
					{
	                    'doc_line': [dl],
	                    'line':[line],
	                    'is_bullet':[0],
	                    'is_name':[0],
	                    'is_org':[0],
	                    'label':[label],
	                    'ents':[0]
	                }
	            )
				detailed = pd.concat([detailed, detail_1], axis=0)
		detailed.reset_index(drop=True, inplace=True)
		return detailed

	def say_status(self):
		'''Shows if DEBUG is True or False.

		Returns:
			Boolean.
		'''
		status = settings.DEBUG
		return status

	def read_resume(self):
		'''Reads a resume.

		Main class method for Resume.

		Returns:
			A csv file with each row labeled.

		'''
	    # Compile text from several files of the same type in a given folder
		print('La Maquina is getting your text...')
		self.text_compiler()
		# Remove unecessary columns
		print('La Maquina is cleaning things up a bit...')
		data = self.clean_text()

		# Create features for use by the ML model
		print('La Maquina is learning English...\t(creating features)')
		data = create_features(data)

		# Write out data for debugging, or for use elsewhere
		print('Writing out clean(er) data with features')
		working_data = self.resume_out_path + self.name + '_working_data.csv'
		data.to_csv(working_data)

		# Run ML model on input text with features included
		print('La Maquina is reading your resume...')
		labeled = self.classify_text(data)

		# Write out data for debugging, or for use elsewhere
		labeled_data = self.resume_out_path + self.name + '_labeled_data.csv'
		labeled.to_csv(labeled_data)

		# Read data back in (??)
		partial = pd.read_csv(self.resume_out_path + self.name + '_labeled_data.csv', sep=',')

		# Start Stanford NLP Server
		print('La Maquina needs more input!...\t(starting server for Stanford ner tagger)\n')
		self.server.start()
		print('La Maquina is connected to the network...\t(server started)')

		# Instantiate a NER tagger
		print('La Maquina is learning more...\t(instantiating a Stanford ner tagger)')
		self.ner_tagger = CoreNLPParser(url = 'http://localhost:9000',\
		 tagtype='ner')
		print('La Maquina is ready to read more of your resume...')
		# Rename unnamed column
		print('La Maquina is labeling data...')
		partial.rename({'Unnamed: 0': 'doc_line'}, axis=1, inplace=True)

		# Label Named Entities using Stanford NER tagger
		partial['label'] = partial.apply(lambda x: self.labeler(x), axis=1)
		print('Data has been labeled.\nShutting down server...')

		# Shutdown server
		self.server.stop()
		print('Server shut down.')

		# Count named entities.
		# Rationale:
		# if the only tag availible is "O", there are no useful tags,
		# if there is only 1 non-"O" tag, than the line gets that tag
		# if there are multiple tags, more processing is needed
		partial['ents'] = partial['label'].apply(lambda x: self.count_named_ents(x))
		partial['label'] = partial.apply(lambda x: self.relabeler(x), axis =1)

		# Write out the data for reference
		ner_labeled_data = self.resume_out_path + self.name + '_ner_labeled_data.csv'
		partial.to_csv(ner_labeled_data)

		print('La Maquina is cleaning things up a bit more...')
		# Break apart the lines with multiple NER tags, by filtering
		# single-word labels from a list. The results is a list of tuples
		# following the pattern [(word, tag), ...]

		# Slice any row with a 'label' not listed in the ResumeParser.keepers
		# attribute.
		keep = partial[~partial['label'].isin(self.keepers)]
		keep.reset_index(drop=True, inplace=True)

		# Make a working copy
		new_df = keep.copy()

		new_df['grouped'] = new_df.label.apply(lambda x: self.tag_grouper(x))

		# Remove the rows with lists of tuples for labels from the labeled
		# DataFrame
		trash = partial[partial['doc_line'].isin(keep.doc_line)].index
		partial.drop(trash, inplace=True)

		# Gather newly made rows into one DataFrame
		loosies = self.get_loosies(new_df)

		# Append the newly made DataFrame to the main DataFrame
		main = pd.concat([partial,loosies], axis=0)

		# Reset the index, so that the newly added rows have higher numbers
		main.reset_index(drop=True, inplace=True)
		# Since 'doc_line' reflects the line from the original document,
		# it can be used to reconstruct the order of the lines. Sorting
		# by it first brings the newly created rows to the proper place
		# on the page. Sorting next by 'm_index', which is the arbitrary
		# name given to the previously unnamed index, will then put the
		# lines in order with their local page neighbors.
		main = main.rename_axis('m_index').sort_values(by=['doc_line', 'm_index'], ascending=[True, True])

		# Write out the fully labeled data
		final_labeled_data = self.resume_out_path + self.name + '_final_labeled_data.csv'
		main.to_csv(final_labeled_data)

		# Print confirmation message, and report how long the process took
		print('La Maquina has printed your results.')
		self.death = datetime.now()
		lifespan = self.death - self.birth
		print('La Maquina read your resume in {} seconds.'\
		.format(lifespan))
		print('You\'re welcome for my service.')
