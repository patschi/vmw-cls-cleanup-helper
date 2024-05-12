# helper-cls-cleanup

This is a small helper written python to clean up VM templates in vSphere Content Library. It re-uses the same CI variables packer accepts, including the same service account to perform actions. Designed to be run as part of the packer pipeline using the docker image.

The cleanup is supposed to identify redundant VM templates in the content library and remove them. The cleanup is based on the following criteria: VM template name and the creation date. It will retain the newest one.
