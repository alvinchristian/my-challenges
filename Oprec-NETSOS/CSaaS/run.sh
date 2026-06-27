#!/bin/bash

socat TCP-LISTEN:8080,reuseaddr,fork EXEC:"sage csaas.sage"