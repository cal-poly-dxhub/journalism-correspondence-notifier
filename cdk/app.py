#!/usr/bin/env python3
import aws_cdk as cdk
from cdk.backend import CorrespondenceNotifierStack


app = cdk.App()
CorrespondenceNotifierStack(app, "CorrespondenceNotifierStack")
app.synth()
