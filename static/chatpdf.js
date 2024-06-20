const uploadInput = document.getElementById('pdf_file');
const fileNameSpan = document.querySelector('.file-name');

uploadInput.addEventListener('change', function(e) {
  const uploadedFile = e.target.files[0];
  if (uploadedFile) {
    fileNameSpan.textContent = uploadedFile.name;
  } else {
    fileNameSpan.textContent = "";
  }
});

document.getElementById('upload_button').addEventListener('click', function() {
  document.getElementById('pdf_file').click();
});

document.getElementById('pdf_file').addEventListener('change', function() {
  var filename = this.files[0].name;
  document.querySelector('.pdf_file').innerText = 'Selected file: ' + filename;
});