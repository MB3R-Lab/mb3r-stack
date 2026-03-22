import org.mb3r.AdapterSupport

def call(Map config = [:]) {
    String outputDir = config.outputDir ?: '.mb3r/bering'
    String payloadPath = "${outputDir}/bering-payload.json"
    String reportPath = "${outputDir}/bering-discovery.json"
    String status = 'pending'
    String artifactName = config.artifactName ?: 'mb3r-bering-discovery'
    int exitCode = 0

    AdapterSupport.ensureDir(this, outputDir)
    exitCode = AdapterSupport.runCommand(
        this,
        config.command ?: '',
        [
            "MB3R_TARGET_PATH=${config.targetPath ?: '.'}",
            "MB3R_PAYLOAD_JSON=${payloadPath}",
            "MB3R_IMAGE_REF=${config.imageRef ?: 'ghcr.io/mb3r-lab/bering@sha256:ac960e908df7fb7defb4ce950d2e54ff8d8f65f7cd5e5f723d424cb425248bad'}"
        ]
    )

    if (config.command?.trim()) {
        status = exitCode == 0 ? 'success' : 'failed'
    }

    Map payload = AdapterSupport.readJson(this, payloadPath)
    if (payload && exitCode == 0) {
        status = 'success'
    }

    Map report = [
        schemaVersion: 'v1alpha1',
        kind: 'mb3r.bering.discovery',
        adapter: 'jenkins-shared-library',
        generatedAt: AdapterSupport.now(),
        targetPath: config.targetPath ?: '.',
        imageRef: config.imageRef ?: 'ghcr.io/mb3r-lab/bering@sha256:ac960e908df7fb7defb4ce950d2e54ff8d8f65f7cd5e5f723d424cb425248bad',
        command: config.command ?: '',
        status: status,
        exitCode: exitCode,
        payloadPath: payloadPath,
        artifactName: artifactName,
        payload: payload ?: null,
    ]

    AdapterSupport.writeJson(this, reportPath, report)
    AdapterSupport.writeEnv(this, "${outputDir}/bering.env", [
        MB3R_BERING_REPORT  : reportPath,
        MB3R_BERING_PAYLOAD : payloadPath,
        MB3R_BERING_ARTIFACT: artifactName,
        MB3R_BERING_STATUS  : status,
    ])

    if (config.archiveArtifacts != false) {
        archiveArtifacts artifacts: "${outputDir}/*", allowEmptyArchive: false
    }

    if (exitCode != 0 && config.failOnError != false) {
        error("mb3rBeringDiscover failed with exit code ${exitCode}")
    }

    return [
        reportPath  : reportPath,
        payloadPath : payloadPath,
        artifactName: artifactName,
        status      : status,
    ]
}
