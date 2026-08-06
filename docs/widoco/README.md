# AIEF Ontology Documentation

Generated with [WIDOCO](https://github.com/dgarijo/Widoco) v1.4.25 from
`ontology/ai-ethics-final.ttl`. Open `doc/index-en.html` in a browser, or
serve this folder at the ontology's persistent URI to give
`https://w3id.org/aief/` a human-readable landing page (with content
negotiation still returning Turtle/RDF to machine clients).

To regenerate after an ontology change:

```bash
java -jar widoco.jar -ontFile ontology/ai-ethics-final.ttl \
  -outFolder docs/widoco -lang en -rewriteAll -webVowl -licensius \
  -noPlaceHolderText
```

## A defect this pass surfaced

Generating documentation runs the ontology through OWLAPI's stricter
parsing than the SHACL/rdflib tooling used elsewhere in this project, and it
surfaced a genuine modelling inconsistency in `:requiresEvidence`: the
property is declared `owl:ObjectProperty` with range `:Evidence`, and used
correctly that way in 3 places (pointing to `:Certificate` /
`:ConsentForm`), but is used with a free-text string literal instead of a
structured `:Evidence` reference in the other 123. Not corrected here, since
resolving it properly means classifying each of those 123 free-text
descriptions against the existing Evidence subclass taxonomy
(`:Certificate`, `:ConsentForm`, `:PIL_ParticipantInfoLeaflet`,
`:GardaVettingCertificate`, `:DPOLetterOfCompletion`,
`:RecruitmentMaterial`, or a new subclass), which is a content decision, not
a mechanical fix, and risks changing the meaning of results already
reported in the dissertation this repository accompanies. Recorded here as
an honest finding and left as a documented item of future ontology work.
