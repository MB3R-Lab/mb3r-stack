package org.mb3r

import groovy.json.JsonOutput
import groovy.json.JsonSlurperClassic
import java.time.Instant

class AdapterSupport implements Serializable {
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

    static void writeJson(script, String path, Map payload) {
        script.writeFile(file: path, text: JsonOutput.prettyPrint(JsonOutput.toJson(payload)) + "\n")
    }

    static void writeEnv(script, String path, Map values) {
        List<String> lines = values.collect { key, value -> "${key}=${value}" }
        script.writeFile(file: path, text: lines.join("\n") + "\n")
    }
}
