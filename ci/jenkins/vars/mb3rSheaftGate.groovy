import org.mb3r.AdapterSupport

def call(Map config = [:]) {
    String outputDir = config.outputDir ?: '.mb3r/sheaft'
    String payloadPath = "${outputDir}/sheaft-payload.json"
    String reportPath = "${outputDir}/sheaft-gate.json"
    String artifactName = config.artifactName ?: 'mb3r-sheaft-gate'
    String decision = config.defaultDecision ?: 'review'
    String status = 'pending'
    int exitCode = 0

    AdapterSupport.ensureDir(this, outputDir)
    exitCode = AdapterSupport.runCommand(
        this,
        config.command ?: '',
        [
            "MB3R_DISCOVERY_REPORT=${config.discoveryReport ?: '.mb3r/bering/bering-discovery.json'}",
            "MB3R_PAYLOAD_JSON=${payloadPath}",
            "MB3R_IMAGE_REF=${config.imageRef ?: 'ghcr.io/mb3r-lab/sheaft@sha256:543771ca12722147578bf7a99dd07c5477c7fe15e7404cf6659a2a02f203a93b'}"
        ]
    )

    if (config.command?.trim()) {
        status = exitCode == 0 ? 'success' : 'failed'
        if (exitCode != 0) {
            decision = 'fail'
        }
    }

    Map payload = AdapterSupport.readJson(this, payloadPath)
    if (payload) {
        decision = payload.decision ?: decision
        if (exitCode == 0) {
            status = 'success'
        }
    }

    Map report = [
        schemaVersion: 'v1alpha1',
        kind: 'mb3r.sheaft.gate',
        adapter: 'jenkins-shared-library',
        generatedAt: AdapterSupport.now(),
        discoveryReport: config.discoveryReport ?: '.mb3r/bering/bering-discovery.json',
        imageRef: config.imageRef ?: 'ghcr.io/mb3r-lab/sheaft@sha256:543771ca12722147578bf7a99dd07c5477c7fe15e7404cf6659a2a02f203a93b',
        command: config.command ?: '',
        decision: decision,
        status: status,
        exitCode: exitCode,
        payloadPath: payloadPath,
        artifactName: artifactName,
        payload: payload ?: null,
    ]

    AdapterSupport.writeJson(this, reportPath, report)
    AdapterSupport.writeEnv(this, "${outputDir}/sheaft.env", [
        MB3R_SHEAFT_REPORT   : reportPath,
        MB3R_SHEAFT_PAYLOAD  : payloadPath,
        MB3R_SHEAFT_ARTIFACT : artifactName,
        MB3R_SHEAFT_STATUS   : status,
        MB3R_SHEAFT_DECISION : decision,
    ])

    if (config.archiveArtifacts != false) {
        archiveArtifacts artifacts: "${outputDir}/*", allowEmptyArchive: false
    }

    if (exitCode != 0 && config.failOnError != false) {
        error("mb3rSheaftGate failed with exit code ${exitCode}")
    }

    return [
        reportPath  : reportPath,
        payloadPath : payloadPath,
        artifactName: artifactName,
        status      : status,
        decision    : decision,
    ]
}
