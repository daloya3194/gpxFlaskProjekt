function set_loading() {
    const input_file = document.getElementById('files');
    if (input_file.files.length > 0) {
        document.getElementById('loading_page').classList.remove('d-none');
    }
}