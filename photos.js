function photoForm() {
  document.getElementById("myPhotoForm").style.display = "block";
}

function closeForm() {
  document.getElementById("myPhotoForm").style.display = "none";
}



// let uploadBtn = document.querySelector("#file-upload");
// uploadBtn.addEventListener("change", addPhoto);

// function addPhoto() {
//   let reader;

//   if (this.files && this.files[0]) {
//     reader = new FileReader();
//     reader.onload = (e) => {
//       photoObject.img.src = e.target.result;
//       drawCanvas();
//     };
//     reader.readAsDataURL(this.files[0]);
//   }
// }

// function head(input) {
//   if (input.files && input.files[0]) {
//     var reader = new FileReader();

//     reader.onload = function(e) {
//       $('#head_shot-img').attr('src', e.target.result);
//     }
//     reader.readAsDataURL(input.files[0]);
//   }
// }

// $("head").change(function() {
//   head(this);
// });

// function side_profile(input) {
//   if (input.files && input.files[0]) {
//     var reader = new FileReader();

//     reader.onload = function(e) {
//       $('#side_profile-img').attr('src', e.target.result);
//     }
//     reader.readAsDataURL(input.files[0]);
//   }
// }

// $('#side_profile').change(function() {
//   side_profile(this);
// });

// function full(input) {
//   if (input.files && input.files[0]) {
//     var reader3 = new FileReader();
//     reader3.onload = function(e) {
//       $('#full-img').attr('src', e.target.result);
//     }
//     reader3.readAsDataURL(input.files[0]);
//   }
// }

// $('full').change(function() {
//   full(this);
// });