import numpy as np
import scipy.stats as stats
import spacy


# ADJ: adjective
# ADP: adposition
# ADV: adverb
# AUX: auxiliary
# CCONJ: coordinating conjunction
# DET: determiner
# INTJ: interjection
# NOUN: noun
# NUM: numeral
# PART: particle
# PRON: pronoun
# PROPN: proper noun
# PUNCT: punctuation
# SCONJ: subordinating conjunction
# SYM: symbol
# VERB: verb
# X: other
pos = spacy.parts_of_speech
POS_OF_INTEREST = [pos.ADJ, pos.ADV, pos.NOUN, pos.PRON, pos.PROPN, pos.VERB, pos.X]
KEY_POS = [pos.NOUN, pos.PROPN]
TOP_N = 5
MODEL = "en_core_web_lg"

CODELIST_FIELDS_TO_LEMMATISE = ["name", "methodology", "description"]


def load_spacy():
    if not spacy.util.is_package(MODEL):
        spacy.cli.download(MODEL)
    return spacy.load(MODEL)


def run_match(bundles, codelists):
    nlp = load_spacy()

    def tag_and_lemmatise(corpus):
        return [
            {
                (token.lemma, token.pos)
                for token in nlp(document.lower())
                if token.pos in POS_OF_INTEREST
            }
            for document in corpus
        ]

    codelist_lemmasets = tag_and_lemmatise(
        [
            ". ".join(
                [
                    codelist[field]
                    for field in CODELIST_FIELDS_TO_LEMMATISE
                    if field in codelist and codelist[field]
                ]
            )
            for codelist in codelists
        ]
    )
    # codelist_lemmasets = lemmatise([codelist["name"] for codelist in codelists])

    bundle_lemmasets = tag_and_lemmatise([bundle["bundle_name"] for bundle in bundles])

    for i, bundle in enumerate(bundles):
        bundle["lemma_jaccard_indices"] = [
            len(bundle_lemmasets[i].intersection(codelist_lemmaset))
            / len(bundle_lemmasets[i])
            if [
                intersection
                for intersection in bundle_lemmasets[i].intersection(codelist_lemmaset)
                if intersection[1] in KEY_POS
            ]
            else 0.0
            for codelist_lemmaset in codelist_lemmasets
        ]
        bundle["refset_jaccard_ranks"] = len(
            bundle["lemma_jaccard_indices"]
        ) - stats.rankdata(bundle["lemma_jaccard_indices"]).astype(int)

    results = []
    for bundle in bundles:
        candidates = [
            (codelists[i], bundle["lemma_jaccard_indices"][int(i)])
            for i in np.where(bundle["refset_jaccard_ranks"] < (TOP_N + 1))[0]
        ]
        results.extend(
            [
                {
                    "bundle_id": bundle["bundle_id"],
                    "bundle_name": bundle["bundle_name"],
                    "codelist_name": candidate[0]["name"],
                    "codelist_url": candidate[0]["url"],
                    "score": candidate[1],
                }
                for candidate in sorted(candidates, key=lambda x: x[1], reverse=True)
            ]
            if candidates
            else [
                {
                    "bundle_id": bundle["bundle_id"],
                    "bundle_name": bundle["bundle_name"],
                    "codelist_name": "None",
                    "codelist_url": "",
                    "score": 0.0,
                }
            ]
        )
    return results
