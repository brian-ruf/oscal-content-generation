# OSCAL Content Generation
Scripts for generating OSCAL content.
The generated content is intended for FedRAMP CI/CD pipeline testing, but could also serve to pre-populate placeholder SSP content when authoring a new SSP based on a FedRAMP baseline.

This is intended to grow over time. 

Current:
- ssp_content_creator.py: 
  - creates `implemented-requirement` assemblies within an existing SSP based on a specified FedRAMP baseline. For each `implemented-requirement`:
    - creates one `set-parameter` assemby for each parameter in the baseline (assigns each a "placeholder" value.)
    - creates one `statement` assembly for each defined response point.
    - creates one `by-component` assembly within each statement, representing the `"this-system"` component 
    - creates a "placeholder" description in each `by-component` assembly.
    - assigns valid UUID values based on a sequence/pattern, suitable for use in example documentation

NOTES: 
- The only FedRAMP-specific aspect of this work is the use of the "response-point" property/FedRAPM extension indicating the statements at which SSP responses are expected. Otherwise, this creates core-OSCAL.
- No profile resolution. This is uses the FedRAMP Resolved Profile Catalog for any baseline. 

Future:
- Generate components
- Generate additional `by-component` and `resource` assemblies to align with required FedRAMP attachments.
- Check for existence of specific controls, components, or resources before creating them. 


