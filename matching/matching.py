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


def _mean_vector(tokens):
    """Average the vectors of tokens that have vectors (skip spaces)."""
    vecs = [t.vector for t in tokens if not t.is_space and t.has_vector]
    if not vecs:
        return None
    return np.mean(vecs, axis=0)


def _load_spacy():
    if not spacy.util.is_package(MODEL):
        spacy.cli.download(MODEL)
    return spacy.load(MODEL)


def run_match(bundles, codelists):
    nlp = _load_spacy()

    def tag_and_lemmatise(corpus):
        return [
            {
                (token.lemma, token.pos)
                for token in nlp(document.lower())
                if token.pos in POS_OF_INTEREST
            }
            for document in corpus
        ]

    codelist_lemma_sets = tag_and_lemmatise(
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

    bundle_lemmasets = tag_and_lemmatise([bundle["bundle_name"] for bundle in bundles])

    def mean_filtered_vector(doc):
        filtered = (t for t in nlp(doc) if t.pos in POS_OF_INTEREST)
        return _mean_vector(filtered)

    codelist_vectors = [
        mean_filtered_vector(codelist["name"]) for codelist in codelists
    ]
    bundle_vectors = [mean_filtered_vector(bundle["bundle_name"]) for bundle in bundles]

    def cosine_simliarity(a, b):
        if a is None or b is None:
            return None
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return None
        return float(np.dot(a, b) / denom)

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
            for codelist_lemmaset in codelist_lemma_sets
        ]
        bundle["codelist_jaccard_ranks"] = len(
            bundle["lemma_jaccard_indices"]
        ) - stats.rankdata(bundle["lemma_jaccard_indices"]).astype(int)
        bundle["mean_filtered_vector_cosines"] = [
            cosine_simliarity(bundle_vectors[i], codelist_vector)
            for codelist_vector in codelist_vectors
        ]
        bundle["codelist_cosine_ranks"] = len(
            bundle["mean_filtered_vector_cosines"]
        ) - stats.rankdata(
            np.array(bundle["mean_filtered_vector_cosines"], dtype=float),
            nan_policy="omit",
        )

    results = []
    for bundle in bundles:
        candidates = [
            (
                codelists[i],
                bundle["lemma_jaccard_indices"][int(i)],
                bundle["codelist_jaccard_ranks"][int(i)],
                bundle["mean_filtered_vector_cosines"][int(i)],
                bundle["codelist_cosine_ranks"][int(i)],
            )
            for i in np.where(
                np.logical_or(
                    bundle["codelist_jaccard_ranks"] < (TOP_N + 1),
                    bundle["codelist_cosine_ranks"] < (TOP_N + 1),
                )
            )[0]
        ]
        results.extend(
            [
                {
                    "bundle_id": bundle["bundle_id"],
                    "bundle_name": bundle["bundle_name"],
                    "codelist_name": candidate[0]["name"],
                    "codelist_url": candidate[0]["url"],
                    "jaccard_score": candidate[1],
                    "jaccard_rank": 1 + int(candidate[2]),
                    "cosine_score": candidate[3],
                    "cosine_rank": 1 + int(candidate[4]),
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
                    "jaccard_score": "",
                    "cosine_score": "",
                    "jaccard_rank": "",
                    "cosine_rank": "",
                }
            ]
        )
    return results
