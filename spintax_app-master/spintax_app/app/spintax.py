from spinrewriterapi import SpinRewriterAPI

# your Spin Rewriter email address goes here
email_address = "admin@botguru.net"

# your unique Spin Rewriter API key goes here
api_key = "f60b6e1#a3befcd_55b7f43?59cd133"

# Spin Rewriter API settings - authentication:
spinrewriter_api = SpinRewriterAPI(email_address, api_key)

#
# (optional) Set a list of protected terms.
# You can use one of the following formats:
# - protected terms are separated by the '\n' (newline) character
# - protected terms are separated by commas (comma-separated list)
# - protected terms are stored in a Python [] array
#
protected_terms = "John, Douglas Adams, then"
# protected_terms = "John\nDouglas\nAdams\nthen"
# protected_terms = ["John", "Douglas", "Adams", "then"]

spinrewriter_api.set_protected_terms(protected_terms)

# (optional) Set whether the One-Click Rewrite process automatically protects
# Capitalized Words outside the article's title.
spinrewriter_api.set_auto_protected_terms(False)

# (optional) Set the confidence level of the One-Click Rewrite process.
spinrewriter_api.set_confidence_level("medium")

# (optional) Set whether the One-Click Rewrite process uses nested spinning syntax (multi-level spinning) or not.
spinrewriter_api.set_nested_spintax(True)

# (optional) Set whether Spin Rewriter rewrites complete sentences on its own.
spinrewriter_api.set_auto_sentences(False)

# (optional) Set whether Spin Rewriter rewrites entire paragraphs on its own.
spinrewriter_api.set_auto_paragraphs(False)

# (optional) Set whether Spin Rewriter writes additional paragraphs on its own.
spinrewriter_api.set_auto_new_paragraphs(False)

# (optional) Set whether Spin Rewriter changes the entire structure of phrases and sentences.
spinrewriter_api.set_auto_sentence_trees(False)

# (optional) Sets whether Spin Rewriter should only use synonyms (where available) when generating spun text.
spinrewriter_api.set_use_only_synonyms(False)

# (optional) Sets whether Spin Rewriter should intelligently randomize the order of paragraphs and lists when
# generating spun text.
spinrewriter_api.set_reorder_paragraphs(False)

# (optional) Sets whether Spin Rewriter should automatically enrich generated articles with headings, bulpoints, etc.
spinrewriter_api.set_add_html_markup(False)

# (optional) Sets whether Spin Rewriter should automatically convert line-breaks to HTML tags.
spinrewriter_api.set_use_html_linebreaks(False)

# Make the actual API request and save the response as a native JSON object.
text = "John will book a room. Then he will read a book by Douglas Adams."


# Make the actual API request and save the response as a native JSON dictionary or False on error
def result(text):
    return spinrewriter_api.get_unique_variation(text)['response']


# o = result(text)
# print(o)
# print(o['response'])
# print(o['status'])
# if result:
#     print("Spin Rewriter API response")
#     print(result)
# else:
#     print("Spin Rewriter API error")


import pandas as pd
import requests
from bs4 import BeautifulSoup
import spacy
from spacy.tokens import Token
import random
import re

noun = {}
verb = {}
adverb = {}
adjective = {}


def webscrapping(word, pos_token):
    url = f'https://www.merriam-webster.com/thesaurus/{word}'
    webpage = requests.get(url).text
    soup = BeautifulSoup(webpage, 'lxml')
    webpage = soup.find_all('div', class_="entry-word-section-container")
    # if not webpage:
    #     pass
    for link in webpage:
        webpage = soup.find_all('div', class_="entry-word-section-container")
        word = soup.find("b", class_="m-0 fw-bold fst-italic").text
        # print(word)

        words = link.find_all('span', class_="thes-list sim-list-scored")

        for syn in words:
            synonyms_list = syn.find_all("span", class_="lozenge color-4")
            pos = link.find_all('a', class_="important-blue-link")
            for pos in pos:

                if (pos.text == "noun") and pos_token == "noun":
                    syn_noun = [word.text for word in synonyms_list]
                    noun[word] = syn_noun
                    # print("NOUN---",syn_noun)

                    return syn_noun

                elif ((pos.text == "verb") or (pos.text == "verb (1)")) and (pos_token == "verb"):

                    # print(pos.text)
                    syn_verb = [word.text for word in synonyms_list]
                    # print("VERB----", syn_verb)
                    verb[word] = syn_verb

                    return syn_verb


                elif pos.text == "adverb":
                    syn_adverb = [word.text for word in synonyms_list]
                    adverb[word] = syn_adverb

                    return syn_adverb
                    # print("VERB----", syn_verb)

                elif pos.text == "adjective":
                    syn_adjective = [word.text for word in synonyms_list]
                    adverb[word] = syn_adjective

                    return syn_adjective
        webpage.clear()


# def generate_spin_options(text):
#     nlp = spacy.load('en_core_web_sm')
#     doc = nlp(text)

#     for token in doc:
#         # print(token, "----", token.pos_.lower())
#         if token.pos_ == "VERB":
#             # print(token.pos_.lower())
#             word = str(token)
#             syn = webscrapping(word, token.pos_.lower())
#             # print(syn)
#             if syn:
#                 random.shuffle(syn)

#                 syn = "{"+ f"{word} | " + " | ".join(syn[:3]) + "}"
#                 pattern = r'\b{}\b'.format(re.escape(word))
#                 text = re.sub(pattern, syn, text)

#                 # text =  text.replace(word,syn)

#         elif token.pos_ == 'NOUN':
#             word = str(token)
#             syn = webscrapping(word, token.pos_.lower())
#             # print(syn)
#             if syn:
#                 random.shuffle(syn)

#                 syn = "{"+ f"{word} | " + " | ".join(syn[:3]) + "}"

#                 pattern = r'\b{}\b'.format(re.escape(word))
#                 text = re.sub(pattern, syn, text)
#     return text

# text = "Hello, What are you doing? Are you going to provide me with any solution for given issue?"
# generated_text = generate_spin_options(text=text)

# def generate_spin_options(text):
#     nlp = spacy.load('en_core_web_sm')
#     doc = nlp(text)
#     modified_tokens = []

#     for token in doc:
#         if token.pos_ == "VERB" or token.pos_ == "NOUN":
#             word = str(token)
#             syn = webscrapping(word, token.pos_.lower())
#             if syn:
#                 # random.shuffle(syn)
#                 modified_tokens.append("{" + f"{word} | " + " | ".join(syn) + "}")
#             else:
#                 modified_tokens.append(word)
#         else:
#             modified_tokens.append(str(token))

#     return " ".join(modified_tokens)


def generate_spin_options(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    modified_tokens = []

    for token in doc:
        if token.pos_ == "VERB" or token.pos_ == "NOUN":
            word = str(token)
            syn = webscrapping(word, token.pos_.lower())
            if syn:
                random.shuffle(syn)
                modified_token = "{" + f"{word} | " + " | ".join(syn[:3]) + "}"
                modified_tokens.append(modified_token)
            else:
                modified_tokens.append(word)
        else:
            modified_tokens.append(str(token))

    modified_text = " ".join(modified_tokens)

    return modified_text


def count_variations_within_braces(text):
    pattern = r'\{([^{}]+)\}'
    matches = re.findall(pattern, text)
    total_variations = 1

    for match in matches:
        options = match.split('|')
        total_variations *= len(options)

    return total_variations


def rewrite_sentence(text):
    # Find all the placeholders within curly braces
    placeholders = re.findall(r'{(.*?)}', text)

    for placeholder in placeholders:
        # Split the options within the placeholder
        options = placeholder.split('|')
        # Choose a random option
        selected_option = random.choice(options).strip()
        # Replace the placeholder with the selected option
        text = text.replace("{" + placeholder + "}", selected_option, 1)

    return text