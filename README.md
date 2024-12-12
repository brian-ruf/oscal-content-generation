# OSCAL Content Generation
Scripts for generating OSCAL content.

This may grow over time. For now, it includes a script for generating SSP content based on a FedRAMP baseline. 

The content is intended for FedRAMP CI/CD pipeline testing, but could also serve to pre-populate placeholder SSP content when authoring a new SSP based on a FedRAMP baseline.

Currently, the only FedRAMP-specific aspect of this work is the use of the "response-point" property/FedRAPM extension indicating the statements at which SSP responses are expected. Otherwise, this creates core-OSCAL.
