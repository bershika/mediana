(function ($) {
		// const fileUploadId = `deposit-fileupload`;
		// const form         = $(`#${fileUploadId}`);
		// const uploadUrl    = form.attr('action');
		// const input        = form.find('input[type="file"]');
		$.fn.dataTable.moment('DD/MM/YY');

		var dt = $('#test-list').DataTable({
			data: [],
			rowId: 'key',
		 	layout:{
				topStart: {
					buttons: ['copy', 'csv', 'excel', 'pdf', 'print']
				}
			},
			columnDefs: [{ type: 'date', targets: 3 }],
			columns: [
				{ data: 'provider', "name": "provider" }, //0
				{ data: 'claim_number', 'name': 'ref number'},
					// render: function(data, type, row) {
					//     // Combine the first and last names into a single table field
					//     return data.patient_first_name + ' ' + data.patient_last_name;
					// }
				//},
				{ data: 'patient_name', name: 'patient name' },
				{ data: "service_date", name: "service date" }, //3
				{ data: "service_description", name: "service description" }, //4
				{ data: "claimed_amount", name: "submitted" }, //5
				{ data: "paid_amount", name: "paid" }, //6
				{ data: "status", name: "claim status" } //7
		  	]
		});

		var getForm = function(box){
			const formContainer = "<form enctype='multipart/form-data'></form>";
			return $(formContainer).html(box.clone());
		};
		var getUploadData = function(form){
			var aForm = getForm(form);
			var ajaxData = new FormData( aForm[0] );

			// if(droppedFiles){
			//     Array.prototype.forEach.call( droppedFiles, function( file ){
			//         ajaxData.append( inputName, file );
			//     });
			// }
			return ajaxData;
		};
		var formSubmit   = function(form){
			var ajaxData = getUploadData(form);
			//var isValidUploadSize = verifyUploadSize(ajaxData);

			// if(!isValidUploadSize){
			//     form.addClass('is-error');
			//     showUploadError(FILE_SIZE_ERROR);
			// }

			// const isEmpty = ajaxData.getAll(inputName).length == 0;
			// if(isEmpty){
			//     form.removeClass('is-uploading');
			//     return false;
			// }
			getAjax(form).send(ajaxData);
		};
		var getAjax = function(form){
			var ajax = new XMLHttpRequest();
			var uploadUrl = form.attr('action');
			ajax.open('POST', uploadUrl, true);

			ajax.onload = function(){
				//form.removeClass( 'is-uploading' );
				if( ajax.status >= 200 && ajax.status < 400 ){

					let data = [];
					let error = '';
					let isSuccess = false;
					let files = false;

					try {
						//todo: test if 'data' present before proceeding
						data = JSON.parse( ajax.responseText )['data'];
						dt.clear();
						dt.rows.add( data ).draw().
						// filter out duplicated lines
						//data = data.filter(item => dt.row(`#${item.key}`).length == 0);

						// data.forEach((line_item) => {
						// 	const row = dt.row(`#${line_item.key}`);
						// 	//const selector = `[id^='${line_item.key}-']`
						// 	//
						// 	console.log(row.length + ' ' + `#${line_item.key}`);

						// 	//item not in the table
						// 	if(!row.length){
						// 		dt.rows.add(data);
						// 		console.log('item not in the table');
						// 	}
						// 	else{
						// 		const claim_claimed_amount = line_item.claimed_amount;
						// 		const claim_paid_amount = line_item.paid_amount;
						// 		const row_data = row.data();
						// 		const row_index = row.index();
						// 		const row_claimed_amount = row_data.claimed_amount;
						// 		const row_paid_amount = row_data.paid_amount;
						// 		dt.cell({row: row_index, column: 7}).data('verified');
						// 	}
						//     //console.log(dt.row(`#${claim.key}`).length);
						// });
						//dt.rows.add(data).draw();
						dt.draw();
						//isSuccess = data.success == true;
						// files = data.files;
						// error = data.error;
					} catch (e) {
						console.log(e);
						// todo: show error
						error = 'Upload failed. You might have been logged out.';
						setTimeout(function(){
							console.log(e);
							//window.location.reload();
						}, 3000);
					}

					//updateNoFileStatus();
				}
				else {
					//form.addClass('is-error');
					//showUploadError('Error. ' + ajax.status + ': '+ ajax.responseText);
				}
			};

			ajax.onerror = function(){
				form.addClass('is-error').removeClass('is-uploading');
				//showUploadError('Upload Request Failed.');
			};
			return ajax;
		};

	$.fn.fileUpload = function(){
		return this.each(function(){
			var fileUploadDiv   = $(this);
			var tableBody       = fileUploadDiv.parents('ul.upload-dd');
			const uploadUrl     = fileUploadDiv.attr('action');
			const input         = fileUploadDiv.find('input[type="file"]');


			// Creates HTML content for the file upload area.
			//var fileDivContent = $('#fileupload');
			//     <label for="${fileUploadId}" class="file-upload">
			//         <div>
			//             <i class="material-icons-outlined">cloud_upload</i>
			//             <p>Drag & Drop Files Here</p>
			//             <span>OR</span>
			//             <div>Browse Files</div>
			//         </div>
			//         <input type="file" id="${fileUploadId}" name=[] multiple hidden />
			//     </label>
			// `;

			// fileUploadDiv.html(fileDivContent).addClass("file-container");


			// Creates a table containing file information.


			// Adds the information of uploaded files to table.
			function handleFiles(files){
				//tableBody.empty();
				if (files.length > 0) {
					$.each(files, function (index, file) {
						const fileName = file.name;
						const fileID = fileName.replace(/\s+/g, '-')
						const fileSize = (file.size / 1024).toFixed(2) + " KB";
						const fileType = file.type;
						var preview = `<img src="${URL.createObjectURL(file)}" alt="${fileName}" height="30">`;
						tableBody.append(`
				<li id="${fileID}"><a href="#" class="flex pl-11 items-center text-sm w-full p-2 text-gray-900 transition duration-75 rounded-lg pl-11 group hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700">
				${fileName}</a></li>`);
			  <!--Delete btn ${preview}-->
			  // <button type="button" class="deleteBtn" class="ms-auto -mx-1.5 -my-1.5 bg-green-50 text-green-500 rounded-lg focus:ring-2 focus:ring-green-400 p-1.5 hover:bg-green-200 inline-flex items-center justify-center h-8 w-8 dark:bg-gray-800 dark:text-green-400 dark:hover:bg-gray-700" data-dismiss-target="#alert-3" aria-label="Close">
			  //   <span class="sr-only">Delete</span>
			  //   <svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
			  //     <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"></path>
			  //   </svg>
			  // </button></li>`);
			});

					tableBody.find(".deleteBtn").click(function () {
						$(this).closest("li").remove();

						// if (tableBody.find("li").length === 0) {
						//     tableBody.append('<li><div class="no-file">No files selected!</td></tr>');
						// }
					});
				}
			}

			// Events triggered after dragging files.
			fileUploadDiv.on({
				dragover: function (e) {
					e.preventDefault();
					fileUploadDiv.toggleClass("dragover", e.type === "dragover");
				},
				drop: function (e) {
					e.preventDefault();
					fileUploadDiv.removeClass("dragover");
					handleFiles(e.originalEvent.dataTransfer.files);
				},
			});

			// Event triggered when file is selected.
			fileUploadDiv.find(`input[type=file]`).change(function () {
				if(! this.files){return;}
				handleFiles(this.files);
				formSubmit(fileUploadDiv);
				$(this).val('');
			});
		});
	};
})(jQuery);
