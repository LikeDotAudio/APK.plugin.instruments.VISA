// Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
// MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
//! `knownDevices.json` — model string → manufacturer, type, notes — as a
//! compile-time string. The JSON file beside this one is the only copy; this
//! crate exists so a plugin can name it by git and build from its own repository.

/// The catalogue, verbatim. Parse it with serde_json in the consumer.
pub const KNOWN_DEVICES_JSON: &str = include_str!("knownDevices.json");

/// `declared.json` — the Rosetta Stone OVERRIDE: locator → the model a person
/// declared is there (and its asset tag), for an instrument that cannot say so
/// itself. Compiled in so a bare image has it; readers prefer an on-disk copy.
pub const DECLARED_JSON: &str = include_str!("declared.json");

#[cfg(test)]
mod tests {
    #[test]
    fn the_catalogue_is_a_non_empty_object_of_models() {
        let t = super::KNOWN_DEVICES_JSON.trim();
        assert!(t.starts_with('{') && t.ends_with('}'), "knownDevices.json is not a JSON object");
        assert!(t.contains("\"type\""), "knownDevices.json names no model type");
    }

    /// Every declaration names a model the catalogue holds (or none, tag only),
    /// and says who declared it and when.
    #[test]
    fn every_declaration_names_a_catalogue_model_and_its_author() {
        let kb: serde_json::Value = serde_json::from_str(super::KNOWN_DEVICES_JSON).unwrap();
        let file: serde_json::Value = serde_json::from_str(super::DECLARED_JSON).expect("declared.json parses");
        assert_eq!(file["schemaVersion"], 1);
        let decls = file["declarations"].as_object().expect("declarations is an object");
        assert!(!decls.is_empty());
        for (locator, d) in decls {
            assert!(!locator.trim().is_empty());
            match d.get("model").and_then(|m| m.as_str()) {
                Some(model) => assert!(kb.get(model).is_some(), "{locator}: model {model} is not in knownDevices.json"),
                None => assert!(d.get("tag").is_some(), "{locator}: neither a model nor a tag"),
            }
            for k in ["declared_by", "declared_at"] {
                assert!(d.get(k).and_then(|v| v.as_str()).is_some_and(|v| !v.is_empty()), "{locator}: no {k}");
            }
        }
        // The owner's declaration (2026-11-05): GPIB 10 on the E5810 is the 3235.
        assert_eq!(decls["TCPIP::44.44.44.222::gpib7,10::INSTR"]["model"], "3235");
    }
}
