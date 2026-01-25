{{/*
Expand the name of the chart.
*/}}
{{- define "ydirect-vbai.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default chart label.
*/}}
{{- define "ydirect-vbai.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | trunc 63 | trimSuffix "-" -}}
{{- end -}}


