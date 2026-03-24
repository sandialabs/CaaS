#!/bin/bash

oc project caas-api && export CAAS_KUBE_JOBS_TOKEN=$(oc create token api-jobs)
