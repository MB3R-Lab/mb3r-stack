{{- define "mb3r-stack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mb3r-stack.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "mb3r-stack.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-stack.labels" -}}
app.kubernetes.io/name: {{ include "mb3r-stack.name" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.global.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "mb3r-stack.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mb3r-stack.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "mb3r-stack.resolveImage" -}}
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

{{- define "mb3r-stack.beringConfigMapName" -}}
{{- if .Values.bering.config.existingConfigMap -}}
{{- .Values.bering.config.existingConfigMap -}}
{{- else -}}
{{- printf "%s-bering-config" (include "mb3r-stack.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-stack.sheaftConfigMapName" -}}
{{- if .Values.sheaft.config.existingConfigMap -}}
{{- .Values.sheaft.config.existingConfigMap -}}
{{- else -}}
{{- printf "%s-sheaft-config" (include "mb3r-stack.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-stack.artifactPVCName" -}}
{{- printf "%s-artifacts" (include "mb3r-stack.fullname" .) -}}
{{- end -}}

{{- define "mb3r-stack.artifactVolumeSource" -}}
{{- if eq .Values.artifacts.volume.type "persistentVolumeClaim" -}}
persistentVolumeClaim:
  claimName: {{ default (include "mb3r-stack.artifactPVCName" .) .Values.artifacts.volume.existingClaim }}
{{- else -}}
emptyDir: {}
{{- end -}}
{{- end -}}

{{- define "mb3r-stack.beringHttpListenAddress" -}}
{{- default (printf ":%v" (.Values.bering.service.ports.http.targetPort | int)) .Values.bering.config.server.listenAddress -}}
{{- end -}}

{{- define "mb3r-stack.beringGrpcListenAddress" -}}
{{- if .Values.bering.service.ports.grpc.enabled -}}
{{- default (printf ":%v" (.Values.bering.service.ports.grpc.targetPort | int)) .Values.bering.config.server.grpcListenAddress -}}
{{- else -}}
{{- default "" .Values.bering.config.server.grpcListenAddress -}}
{{- end -}}
{{- end -}}

{{- define "mb3r-stack.beringServiceName" -}}
{{- printf "%s-bering" (include "mb3r-stack.fullname" .) -}}
{{- end -}}

{{- define "mb3r-stack.sheaftServiceName" -}}
{{- printf "%s-sheaft" (include "mb3r-stack.fullname" .) -}}
{{- end -}}

{{- define "mb3r-stack.beringPublicServiceName" -}}
{{- default (include "mb3r-stack.beringServiceName" .) .Values.bering.service.publicName -}}
{{- end -}}

{{- define "mb3r-stack.sheaftPublicServiceName" -}}
{{- default (include "mb3r-stack.sheaftServiceName" .) .Values.sheaft.service.publicName -}}
{{- end -}}

{{- define "mb3r-stack.beringEndpoint" -}}
{{- if .Values.collector.targetEndpoint -}}
{{ .Values.collector.targetEndpoint }}
{{- else -}}
{{ printf "http://%s:%v" (include "mb3r-stack.beringPublicServiceName" .) (.Values.bering.service.ports.http.port | int) }}
{{- end -}}
{{- end -}}
