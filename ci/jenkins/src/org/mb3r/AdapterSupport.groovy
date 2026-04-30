package org.mb3r

import groovy.json.JsonOutput
import groovy.json.JsonSlurperClassic
import java.time.Instant

class AdapterSupport implements Serializable {
    static final Set<String> ALLOWED_DECISIONS = ['fail', 'pass', 'report', 'review', 'warn'] as Set

    static String now() {
        return Instant.now().toString()
    }

    static void ensureDir(script, String path) {
        if (script.isUnix()) {
            script.sh(script: "mkdir -p \"${path}\"")
        } else {
            script.bat(script: "if not exist \"${path}\" mkdir \"${path}\"")
        }
    }

    static int runCommand(script, String command, List<String> envPairs) {
        if (!(command?.trim())) {
            return 0
        }
        script.withEnv(envPairs) {
            if (script.isUnix()) {
                return script.sh(script: command, returnStatus: true)
            }
            return script.bat(script: command, returnStatus: true)
        }
    }

    static Map readJson(script, String path) {
        if (!script.fileExists(path)) {
            return [:]
        }
        return new JsonSlurperClassic().parseText(script.readFile(path)) as Map
    }

    static String normalizeDecision(Object value, String source) {
        String decision = value?.toString()
        if (!ALLOWED_DECISIONS.contains(decision)) {
            String allowed = ALLOWED_DECISIONS.toList().sort().join(', ')
            throw new IllegalArgumentException("${source} decision must be one of ${allowed}: ${value}")
        }
        return decision
    }

    static void writeJson(script, String path, Map payload) {
        script.writeFile(file: path, text: JsonOutput.prettyPrint(JsonOutput.toJson(payload)) + "\n")
    }

    static void writeEnv(script, String path, Map values) {
        List<String> lines = values.collect { key, value -> "${key}=${value}" }
        script.writeFile(file: path, text: lines.join("\n") + "\n")
    }
}
