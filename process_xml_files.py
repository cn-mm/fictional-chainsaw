# Run with python 3
'''
To generate document, document lemma and summary files for each bbc article
'''
import json
import os
import xml.etree.ElementTree as ET
import itertools
import argparse

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Parse xml files')
  parser.add_argument('--stanford_dir', type=str, default="./StanfordOutput")
  parser.add_argument('--split_dict', type=str, default="new_split.json")
  parser.add_argument('--output_dir', type=str, default="./xsum-preprocessed")
  args = parser.parse_args()

  stanford_directory = args.stanford_dir
  split_file = args.split_dict

  # Load split file
  split_dict = json.loads(open(split_file).read())
  data_types = ["test", "validation", "train"]

  output_directory = args.output_dir
  if not os.path.exists(output_directory):
    os.mkdir(output_directory)
    print("op dir created")
  # os.system("mkdir -p "+output_directory)

  count = 1
  for dtype in data_types:
    print(dtype)
    
    if not os.path.exists(output_directory+"/document"): 
      os.mkdir(output_directory+"/document")
    if not os.path.exists(output_directory+"//document-lemma"): 
      os.mkdir(output_directory+"/document-lemma")
    if not os.path.exists(output_directory+"//summary"): 
      os.mkdir(output_directory+"/summary")
    
    for orgfileid in split_dict[dtype]:

      if (os.path.isfile(output_directory+"/document/"+orgfileid+".document") and
          os.path.isfile(output_directory+"/document-lemma/"+orgfileid+".document-lemma") and
          os.path.isfile(output_directory+"/summary/"+orgfileid+".summary")):
        continue

      # print(orgfileid)
      
      stanfordfile = stanford_directory + "/" + orgfileid + ".data.xml"
    
      doc_sentences = []
      doc_sentlemmas = []
      # process xml file
      tree = ET.parse(stanfordfile)
      root = tree.getroot()
       
      i =0
      for sentences in root.iter('sentences'):
          for sentence in sentences.iter('sentence'):
              # print(sentence.attrib)
              sentence_tokenized = []
              sentence_lemmatized = []
              for token in sentence.iter('token'):
                  word = token.find('word').text
                  sentence_tokenized.append(word)
                  lemma = token.find('lemma').text
                  sentence_lemmatized.append(lemma)
              # Fixing the XUM INTRODUCTION in next line error
              # TODO: find why it is occuring 
              if i ==0:
                substr = substring = "[ XSUM ] INTRODUCTION [ XSUM ]"
                sent = " ".join(sentence_tokenized)
                sent_lem = " ".join(sentence_lemmatized)
                if sent.find(substring) != -1:
                    pos = sent.find(substring)
                    doc_sentences.append(sent[:pos])
                    doc_sentences.append(sent[pos:])
                    doc_sentlemmas.append(sent_lem[:pos])
                    doc_sentlemmas.append(sent_lem[pos:])
                i+=1
              doc_sentences.append(" ".join(sentence_tokenized))
              doc_sentlemmas.append(" ".join(sentence_lemmatized))
              
      # print("S1:",doc_sentences[0])
      # print("S2",doc_sentences[1])
      # print(doc_sentences[2])
      doc_sentences[2] = ""

      # Extract data
      modeFlag = None

      restbodydata = []
      restbodylemmadata = []
      summarydata = []
      
      allcovered = 0
      for doc_sent, doc_sentlemma in zip(doc_sentences, doc_sentlemmas):
        # print("Pair:", doc_sent, doc_sentlemma)
        if "[ XSUM ] URL [ XSUM ]" in doc_sent:
          modeFlag = "URL"
          allcovered += 1
        elif "[ XSUM ] INTRODUCTION [ XSUM ]" in doc_sent:
          modeFlag = "INTRODUCTION"
          allcovered += 1
          summarydata.append(doc_sent[30:]) # Starting after [ XSUM ]
        elif "[ XSUM ] RESTBODY [ XSUM ]" in doc_sent:
          modeFlag = "RestBody"
          allcovered += 1
        else:
          if modeFlag == "RestBody":
            restbodydata.append(doc_sent)
            restbodylemmadata.append(doc_sentlemma)
          if modeFlag == "INTRODUCTION":
            # print(doc_sent)
            # print("intro found")
            summarydata.append(doc_sent)

      print("All 3 generated!")
      if allcovered != 3:
        print("Some information missing", stanfordfile)
        # print("\n".join(doc_sentences))
        exit(0)

      # rest body data
      foutput = open(output_directory+"/document/"+orgfileid+".document", "w")
      foutput.write("\n".join(restbodydata)+"\n")
      foutput.close()
      
      # rest body lemma data
      foutput = open(output_directory+"/document-lemma/"+orgfileid+".document-lemma", "w")
      foutput.write("\n".join(restbodylemmadata)+"\n")
      foutput.close()

      # summary data
      foutput = open(output_directory+"/summary/"+orgfileid+".summary", "w")
      foutput.write("\n".join(summarydata)+"\n")
      foutput.close()
      
      if count%1000 == 0:
          print(count)
      count += 1
      
      # exit(0)
    

 
