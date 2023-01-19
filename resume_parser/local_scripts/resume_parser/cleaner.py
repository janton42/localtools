import re
import string
import nltk
import os
import pandas as pd
from django.conf import settings
# from sklearn.preprocessing import LabelBinarizer


# Constants and instantiations
stopwords = nltk.corpus.stopwords.words('english')
ps = nltk.PorterStemmer()
wn = nltk.WordNetLemmatizer()
verb_tags = ['VB','VBG','VBD', 'VBN','VBN-HL','VERB']
adj_tags = ['JJ', 'JJR','JJS']
symbol_tags = ['SYM']
list_tags = ['LS']
determiner_tags = ['DT']
name_path = os.path.join(settings.ENTITIES_PATH, 'freq_names.csv')
name_list = pd.read_csv(name_path)
names = name_list.name.unique()
company_path = os.path.join(settings.ENTITIES_PATH, 'companies.csv')
company_list = pd.read_csv(company_path)
companies = company_list.trimmed_name.unique()

def remove_stopwords(text):
    text = ''.join([word for word in text if word not in string.punctuation])
    tokens = re.split('\W+',text)
    text = [word for word in tokens if word not in stopwords]
    return text

def get_stems(tokenized_text):
    text = [ps.stem(word) for word in tokenized_text]
    return tokenized_text

def count_words(text):
    text = ''.join([word for word in text if word not in string.punctuation])
    tokens = re.split('\W+',text)
    return len(tokens)

def count_verbs(pos_tags: list) -> int:
    count = sum([1 for pair in pos_tags if pair[1] in verb_tags])
    return round(count/(len(pos_tags)),3)*100 if len(pos_tags) > 0 else 0

def count_adj(pos_tags: list) -> int:
    count = sum([1 for pair in pos_tags if pair[1] in adj_tags])
    return round(count/(len(pos_tags)),3)*100 if len(pos_tags) > 0 else 0

def count_nums(pos_tags: list) -> int:
    count = sum([1 for pair in pos_tags if pair[1] == 'CD'])
    return round(count/(len(pos_tags)),3)*100 if len(pos_tags) > 0 else 0

def count_proper_nouns(pos_tags: list) -> int:
    count = sum([1 for pair in pos_tags if pair[1] == 'NNP'])
    return round(count/(len(pos_tags)),3)*100 if len(pos_tags) > 0 else 0

def count_stopwords(line: str) -> int:
    count = sum([1 for word in nltk.word_tokenize(line) if word in nltk.corpus.stopwords.words('english')])
    return round(count/(len(line) - line.count(' ')),3)*100 if len(line) > 0 else 0

def count_punct(line: str) -> int:
    count = sum([1 for char in line if char in string.punctuation])
    return round(count/(len(line) - line.count(' ')), 3)*100 if len(line) > 0 else 0

def count_symbols(line: str) -> int:
    count = sum([1 for pair in line if pair[1] in symbol_tags])
    return round(count/(len(line)),3)*100 if len(line) > 0 else 0

def count_list_item_markers(line: str) -> int:
    count = sum([1 for pair in line if pair[1] in list_tags])
    return round(count/(len(line)),3)*100 if len(line) > 0 else 0

def count_determiners(line: str) -> int:
    count = sum([1 for pair in line if pair[1] in determiner_tags])
    return round(count/(len(line)),3)*100 if len(line) > 0 else 0

def count_names(line: str) -> int:
    count = sum([1 for name in line if name in names])
    return count

def count_companies(line: str) -> int:
    count = sum([1 for company in line if company in companies])
    return count

def create_features(data):
    # Remove stop words
    data['line_nostop'] = data['line'].apply(lambda x: remove_stopwords(x.lower()))

    # Collect the word stems
    data['line_stemmed'] = data['line_nostop'].apply(lambda x: get_stems(x))

    # Find line length
    data['line_length'] = data['line'].apply(lambda x: len(x) - x.count(' '))

    # Find word count per line
    data['word_count'] = data['line'].apply(lambda x: count_words(x))

    # Tag each line with parts of speach
    data['tagged_line'] = data['line'].apply(lambda x: nltk.pos_tag(nltk.word_tokenize(x)))

    # Find the percentage of verbs in each line
    data['verb_percentage'] = data['tagged_line'].apply(lambda x: count_verbs(x))

    # Find the percentage of adjectives in each line
    data['adj_percentage'] = data['tagged_line'].apply(lambda x: count_adj(x))

    # Find the percentage of stop words in each line
    data['stopword_percentage'] = data['line'].apply(lambda x: count_stopwords(x))

    # Find the percentage of punctuation in each line
    data['punctuation_percentage'] = data['line'].apply(lambda x: count_punct(x))

    # Find the percentage of numbers in each line
    data['number_percentage'] = data['tagged_line'].apply(lambda x: count_nums(x))

    # Find the percentage of numbers in each line
    data['proper_noun_percentage'] = data['tagged_line'].apply(lambda x: count_proper_nouns(x))

    # Count symbols in each line
    data['symbol_count'] = data['tagged_line'].apply(lambda x: count_symbols(x))

    # Count list item markers in each line
    data['list_markers_count'] = data['tagged_line'].apply(lambda x: count_list_item_markers(x))

    # Count determiners in each line
    data['determiners_count'] = data['tagged_line'].apply(lambda x: count_determiners(x))

    # Count names in each line
    data['name_count'] = data['line_nostop'].apply(lambda x: count_names(x))

    data['line_length_trans'] = data['line_length'].apply(lambda x : x**(1/5))

    data['word_count_trans'] = data['word_count'].apply(lambda x : x**(1/3))

    data['verb_percentage_trans'] = data['verb_percentage'].apply(lambda x : x**(1/2))

    data['adj_percentage_trans'] = data['adj_percentage'].apply(lambda x : x**(1/2))

    data['stopword_percentage_trans'] = data['stopword_percentage'].apply(lambda x : x**(1/2))

    data['punctuation_percentage_trans'] = data['punctuation_percentage'].apply(lambda x : x**(1/2))

    data['number_percentage_trans'] = data['number_percentage'].apply(lambda x : x**(1/1))

    data['proper_noun_percentage_trans'] = data['proper_noun_percentage'].apply(lambda x : x**(1/1))

    # Count company names in each line
    data['company_count'] = data['line_nostop'].apply(lambda x: count_companies(x))

    return data
