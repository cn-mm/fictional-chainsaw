# fictional-chainsaw
Don't give me the details, just the summary



# Instructions

Before running the script lda-gensim-training-document-lemma.py, download the stopwords using nltk separately.
```sh
import nltk
nltk.download('stopwords')
```
Afterwards, modify the path in line 23 of lda-gensim-training-document-lemma.py, i.e., the variable file_stop. Then run the below command.
```sh
python lda-gensim-training-document-lemma.py 512 1000 > lda-train.log 2> lda-train.log.2
```

