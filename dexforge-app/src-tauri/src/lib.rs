// Indigo Dexforge — Tauri shell.
// The app is a local asset viewer: the whole sprite vault, every character and action
// sheet, and the animation player. No network, no API keys, nothing bundled that needs one.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // External links are dead in a Tauri webview without this.
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("error while running Indigo Dexforge");
}
