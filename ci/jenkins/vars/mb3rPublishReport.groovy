import groovy.json.JsonOutput
import groovy.json.JsonSlurperClassic
import org.mb3r.AdapterSupport

def call(Map config = [:]) {
    String outputDir = config.outputDir ?: '.mb3r/report'
    String reportJsonPath = "${outputDir}/mb3r-report.json"
    String reportMarkdownPath = "${outputDir}/mb3r-report.md"
    String artifactName = config.artifactName ?: 'mb3r-report'

    AdapterSupport.ensureDir(this, outputDir)

    Map discovery = new JsonSlurperClassic().parseText(readFile(config.discoveryReport ?: '.mb3r/bering/bering-discovery.json')) as Map
    Map gate = new JsonSlurperClassic().parseText(readFile(config.gateReport ?: '.mb3r/sheaft/sheaft-gate.json')) as Map
    String overallDecision = gate.decision ?: 'review'

    Map report = [
        schemaVersion: 'v1alpha1',
        kind: 'mb3r.stack.report',
        adapter: 'jenkins-shared-library',
        generatedAt: AdapterSupport.now(),
        overallDecision: overallDecision,
        discovery: [
            status: discovery.status,
            path: config.discoveryReport ?: '.mb3r/bering/bering-discovery.json',
            artifactName: discovery.artifactName,
        ],
        gate: [
            decision: gate.decision,
            status: gate.status,
            path: config.gateReport ?: '.mb3r/sheaft/sheaft-gate.json',
            artifactName: gate.artifactName,
        ],
    ]

    writeFile file: reportJsonPath, text: JsonOutput.prettyPrint(JsonOutput.toJson(report)) + "\n"
    writeFile file: reportMarkdownPath, text: """# MB3R Report

- Generated at: ${report.generatedAt}
- Discovery status: ${report.discovery.status}
- Gate status: ${report.gate.status}
- Overall decision: ${overallDecision}
"""

    AdapterSupport.writeEnv(this, "${outputDir}/mb3r-report.env", [
        MB3R_REPORT_JSON    : reportJsonPath,
        MB3R_REPORT_MARKDOWN: reportMarkdownPath,
        MB3R_REPORT_ARTIFACT: artifactName,
        MB3R_OVERALL_DECISION: overallDecision,
    ])

    if (config.archiveArtifacts != false) {
        archiveArtifacts artifacts: "${outputDir}/*", allowEmptyArchive: false
    }

    return [
        reportJson     : reportJsonPath,
        reportMarkdown : reportMarkdownPath,
        artifactName   : artifactName,
        overallDecision: overallDecision,
    ]
}
