// Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
// MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
//! `knownDevices.json` — model string → manufacturer, type, notes — as a
//! compile-time string. The JSON file beside this one is the only copy; this
//! crate exists so a plugin can name it by git and build from its own repository.

/// The catalogue, verbatim. Parse it with serde_json in the consumer.
pub const KNOWN_DEVICES_JSON: &str = include_str!("knownDevices.json");

#[cfg(test)]
mod tests {
    #[test]
    fn the_catalogue_is_a_non_empty_object_of_models() {
        let t = super::KNOWN_DEVICES_JSON.trim();
        assert!(t.starts_with('{') && t.ends_with('}'), "knownDevices.json is not a JSON object");
        assert!(t.contains("\"type\""), "knownDevices.json names no model type");
    }
}
