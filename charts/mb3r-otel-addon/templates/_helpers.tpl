{{- define "mb3r-otel-addon.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mb3r-otel-addon.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "mb3r-otel-addon.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-otel-addon.labels" -}}
app.kubernetes.io/name: {{ include "mb3r-otel-addon.name" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.global.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "mb3r-otel-addon.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mb3r-otel-addon.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "mb3r-otel-addon.resolveImage" -}}
{{- $root := .root -}}
{{- $image := .image -}}
{{- $registry := coalesce $image.registry $root.Values.global.imageRegistry -}}
{{- if $image.digest -}}
{{- if $registry -}}
{{ printf "%s/%s@%s" $registry $image.repository $image.digest }}
{{- else -}}
{{ printf "%s@%s" $image.repository $image.digest }}
{{- end -}}
{{- else -}}
{{- $tag := default $root.Chart.AppVersion $image.tag -}}
{{- if $registry -}}
{{ printf "%s/%s:%s" $registry $image.repository $tag }}
{{- else -}}
{{ printf "%s:%s" $image.repository $tag }}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-otel-addon.beringConfigMapName" -}}
{{- if .Values.bering.config.existingConfigMap -}}
{{- .Values.bering.config.existingConfigMap -}}
{{- else -}}
{{- printf "%s-bering-config" (include "mb3r-otel-addon.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-otel-addon.sheaftConfigMapName" -}}
{{- if .Values.sheaft.config.existingConfigMap -}}
{{- .Values.sheaft.config.existingConfigMap -}}
{{- else -}}
{{- printf "%s-sheaft-config" (include "mb3r-otel-addon.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-otel-addon.artifactPVCName" -}}
{{- printf "%s-artifacts" (include "mb3r-otel-addon.fullname" .) -}}
{{- end -}}

{{- define "mb3r-otel-addon.artifactVolumeSource" -}}
{{- if eq .Values.artifacts.volume.type "persistentVolumeClaim" -}}
persistentVolumeClaim:
  claimName: {{ default (include "mb3r-otel-addon.artifactPVCName" .) .Values.artifacts.volume.existingClaim }}
{{- else -}}
emptyDir: {}
{{- end -}}
{{- end -}}

{{- define "mb3r-otel-addon.beringHttpListenAddress" -}}
{{- default (printf ":%v" (.Values.bering.service.ports.http.targetPort | int)) .Values.bering.config.server.listenAddress -}}
{{- end -}}

{{- define "mb3r-otel-addon.beringGrpcListenAddress" -}}
{{- if .Values.bering.service.ports.grpc.enabled -}}
{{- default (printf ":%v" (.Values.bering.service.ports.grpc.targetPort | int)) .Values.bering.config.server.grpcListenAddress -}}
{{- else -}}
{{- default "" .Values.bering.config.server.grpcListenAddress -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-otel-addon.beringEndpoint" -}}
{{- if .Values.collector.targetEndpoint -}}
{{ .Values.collector.targetEndpoint }}
{{- else -}}
{{ printf "http://%s-bering:%v" (include "mb3r-otel-addon.fullname" .) (.Values.bering.service.ports.http.port | int) }}
{{- end -}}
{{- end -}}
