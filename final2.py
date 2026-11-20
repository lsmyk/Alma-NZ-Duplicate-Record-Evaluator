# -*- coding: utf-8 -*-
#processing dups to share.ipynb


import os
import re
import pandas as pd
from pymarc import MARCReader, MARCWriter, Record
import numpy as np

#To run Stacie code to evaluate MARC records




#
def rec_eval(file):

	with open(file,'rb') as f:

		reader = MARCReader(f)

		record_dict = {}

		rec_count = 0

		for rec in reader:
			
			#get record elements for completness evaluation
			rec_id = rec.get_fields('001')
			field_008 = rec.get_fields('008')
			isbn = rec.get_fields('020')
			rec_source = rec.get_fields('040')
			classif = rec.get_fields('050', '060', '090')
			authors = rec.get_fields('100', '110', '111')
			title = rec.get_fields('245')
			#st_of_resp = title.get_subfields('c')
			alt_titles = rec.get_fields('246')
			edition = rec.get_fields('250')
			imprint = rec.get_fields('260', '264')
			descr = rec.get_fields('300')
			toc = rec.get_fields('505')
			abstract = rec.get_fields('520')
			subjects = rec.get_fields('600', '610', '611', '630',
				'650', '651', '653')
			contribs = rec.get_fields('700', '710', '711', '720')
			series = rec.get_fields('440', '490', '800', '810', '830')

			rec_qualities = {}

			#extract value of 001 field
			record_id = str(rec_id[0]).lstrip('=001  ')
			
			#add simple count to dict for some elements CANNOT BE DONE BECAUSE AttributeError: 'list' object has no attribute 'get_subfields'
			rec_qualities['isbn_count'] = len(isbn)
			#rec_qualities ['st_of_resp_count'] = len(st_of_resp)
			rec_qualities['authors'] = len(authors)
			rec_qualities['alt_titles'] = len(alt_titles)
			rec_qualities['edition'] = len(edition)
			rec_qualities['contribs'] = len(contribs)
			rec_qualities['series'] = len(series)
			
			#check for toc and abstract
			if toc and abstract:
				rec_qualities['toc_abstract'] = 2
			elif toc or abstract:
				rec_qualities['toc_abstract'] = 1
			else:
				rec_qualities['toc_abstract'] = 0

			#get dates from 008 and 26X if they exist
			date_008 = re.findall('^.{13}([0-9]{2}[0-9u]{2}).*$', str(field_008[0]))
			rec_qualities['date_008'] = len(date_008)
			if not date_008:
				date_008 = [1111]
			
			date_imprint = ['0']
			rec_qualities['date_26X'] = 0
			if imprint:
				subf_c_26X = [field.get_subfields('c') for field in imprint]
				try:
					date_imprint_list = re.findall('^.*(\d{4}).*$', str(subf_c_26X[0]))
					date_imprint[0] = date_imprint_list[0]
					rec_qualities['date_26X'] = 1
				except IndexError:
					date_imprint = ['0']

			try:
				date_008_int = int(date_008[0])
			except ValueError:
				date_008_int = 1111

			#evaluate whether 008 and 26X dates match
			if date_008_int == int(date_imprint[0]):
				rec_qualities['dates_matched'] = 1
			else:
				rec_qualities['dates_matched'] = 0

			#check for LC or NLM classification
			if classif:
				rec_qualities['classification'] = 1
			else:
				rec_qualities['classification'] = 0

			#parse and count subject fields based on indicators and vocabulary codes
			lcsh_count = 0
			mesh_count = 0
			fast_count = 0
			othersub_count = 0
			lcsh_re = re.compile('^.{7}0.*$')
			mesh_re = re.compile('^.{7}2.*$')
			fast_re = re.compile('^.{7}7.*2fast.*$')
			for subj in subjects:
				if lcsh_re.match(str(subj)):
					lcsh_count += 1
				elif mesh_re.match(str(subj)):
					mesh_count += 1
				elif fast_re.match(str(subj)):
					fast_count += 1
				else:
					othersub_count += 1
			if lcsh_count < 10:
				rec_qualities['subjects_lcsh'] = lcsh_count
			else:
				rec_qualities['subjects_lcsh'] = 10
			if mesh_count < 10:
				rec_qualities['subjects_mesh'] = mesh_count
			else:
				rec_qualities['subjects_mesh'] = 10
			if fast_count < 10:
				rec_qualities['subjects_fast'] = fast_count
			else:	
				rec_qualities['subjects_fast'] = 10
			if othersub_count < 5:
				rec_qualities['subjects_other'] = othersub_count
			else:
				rec_qualities['subjects_other'] = 5


			#get values from 245 $c if they exist
			
			st_of_resp = ['0']
			rec_qualities['st_of_resp'] = 0
			if title:
				try:
					st_of_resp_list = re.findall('^.*\$c.*',str (title[0]))
					st_of_resp[0] = st_of_resp_list[0]
					rec_qualities['st_of_resp'] = 1
				except IndexError:
					st_of_resp = ['0']


			#check if resource language code exists
			rsrc_lang_re = re.compile('^.{41}[a-z]{3}.*$')
			if rsrc_lang_re.match(str(field_008[0])):
				rec_qualities['rsrc_lang'] = 1
			else:
				rec_qualities['rsrc_lang'] = 0

			#check if country code exists
			ctry_code_re = re.compile('^.{21}([a-z]{2})|([a-z]{3}).*$')
			if ctry_code_re.match(str(field_008[0])):
				rec_qualities['ctry_code'] = 1
			else:
				rec_qualities['ctry_code'] = 0

			#check language of cataloging and explicit rda status
			cat_lang_re = re.compile('^.*eng.*$')
			rda_re = re.compile('^.*erda.*$')
			for field in rec_source:
				subf_b_040 = field.get_subfields('b')
				if subf_b_040 and not cat_lang_re.match(str(subf_b_040)):
					rec_qualities['cat_lang'] = 0
				else:
					rec_qualities['cat_lang'] = 1
				if rda_re.match(str(field)):
					rec_qualities['rda'] = 1
				else:
					rec_qualities['rda'] = 0

			rec_score = 0
			for k, v in rec_qualities.items():
				rec_score = rec_score + v
			rec_qualities['total_rec_score'] = rec_score

			record_dict[record_id] = rec_qualities

			rec_count += 1

	return record_dict, rec_count

def record_dict_to_csv(record_dict, record_count, fpref):

  with open(fpref + '_rates.csv', 'w') as out:
      #make dataframe from record_dict and replace NaN values
      df = pd.DataFrame.from_dict(record_dict, orient='index')
      df = df.fillna(value=0)
      df['mean'] = df.total_rec_score.mean()
      df['stdev'] = df.total_rec_score.std()
      df['count'] = record_count

           
      df = df.sort_values(['mean', 'stdev'])
      df.to_csv(out)
      
  return df


#get file 
files = [f for f in os.listdir() if re.match(r'.+\.mrc', f)]
file = 'bibs.mrc'

#function calls
for file in files:
	fpref, fsuf = file.split('.')
	record_dict, record_count = rec_eval(file)
	record_dict_to_csv(record_dict, record_count, fpref)

#Read .csv file from Alex spreadsheet (dups) NOT SURE IF I HAVE TO ADD A PARTICULAR ENCODING HERE such as ,encoding = "ISO-8859–1"
df_dups = pd.read_csv("dups.csv")

#To dedup by MMS Id
df_dups = df_dups.drop_duplicates(subset='MMS Id', keep="first")

#Read .csv file from previouse script (bibs_rates)). Rename "Unnamed" to "MMS Id. Select only 2 columns: "MMS Id" and "total_rec_score
df_rates = pd.read_csv("bibs_rates.csv",encoding="ISO-8859-1")
df_rates.rename( columns={'Unnamed: 0':'MMS Id'}, inplace=True )
df_rates = df_rates[["MMS Id", "total_rec_score"]]

#Merge .csv files
df = df_dups.merge(df_rates, how='left', on='MMS Id')

#Add column for "Group #"
df['Group #'] = df.groupby(['Identifier']).ngroup()+1


#To create column for "Records in Groups"
##add column with max rates
df['max'] = df.groupby('Group #')['total_rec_score'].transform('max')

#Group and sort permanently (create a new index) by "Group #" first and "total_rec_score" second
df_s=df.sort_values(['Group #', 'total_rec_score'], ascending=False).reset_index(drop=True)

#count records in groups
df_s['Records in Group'] = df_s.groupby(['Group #']).cumcount()+1


#Define records as "preferred" and to be "merge"
#list conditions
conditions =[
  (df_s['total_rec_score']==df_s['max']) & (df_s['Records in Group']==1),
  (df_s['total_rec_score']==df_s['max']) & (df_s['Records in Group']!=1),
  (df_s['total_rec_score']!=df_s['max'])
       ]
values = ['preferred', 'merge','merge']
df_s['Operation'] = np.select(conditions, values, default='preferred')

#Drop 'total rec score' 'max' columns
del df_s['total_rec_score']
del df_s['max']

#To order columns as : Group Number, MMS ID, Identifier, Records in Group, Operation, Material Type, Brief Level, Resource Type, Institution Name, Title#

df_f=df_s.iloc[:, [7,0,1,8,9,2,3,4,5,6]]

#to export the file
df_f.to_csv(r'C:\Users\lsmyk\OneDrive - University of Waterloo\Desktop\Python test\'merge.csv', index=False)


