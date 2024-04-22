var REQUISITION = REQUISITION || {};

REQUISITION.FileUpload = (function(){
	const KB = 1024;
	const MAX_FILE_SIZE = 45 * KB * KB;
	const FILE_SIZE_ERROR = "Upload size must be less than 45MB.";

	let isAffectedInputName = null,
		deleteModal = null,
		filesList = null,
		noFilesRow = null,
		errorBox = null;

	// feature detection for drag&drop upload
	var isAdvancedUpload = function(){
		var div = document.createElement( 'div' );
		return ( ( 'draggable' in div ) || ( 'ondragstart' in div && 'ondrop' in div ) ) && 'FormData' in window && 'FileReader' in window;
	}();

	var getUploadedFiletRow = function(fileId, fileName){
		if(!fileId) {
			return $('<li class="list-group-item text-left">' +
				'<span>' + fileName + '</span>' +
				'<span>Failed to upload</span>' +
				'</li>');
		}
		return  $('<li class="list-group-item text-left" data-id="' + fileId + '">' +
			'<span class="file-name">' + fileName + '</span>' +
			//'<div class="status-updating">Deleting&hellip;</div>' +
			//getDeleteFileLink(fileId, fileName) +
			'</li>');
	};
	var getDeleteFileLink = function(fileId, fileName){
		return '<a class="delete-file-link pull-right" href="#delete-file-modal" data-toggle="modal">' +
		'<i class="fa fa-close text-danger"></i>'+
		'</a>';
	};
	var showUploadedFiles = function(resultBox, files){
		//sanitize files
		for(let fileId in files){
			fileName = files[fileId];
			getUploadedFiletRow(fileId, fileName).appendTo(resultBox);
		};
	};
	var updateNoFileStatus = function(){
		let filesCount = filesList.find('li:not(.empty-list)').length;
		if(filesCount){ noFilesRow.hide(); }
		else{ noFilesRow.show(); }
	};
	var isValidFileSize = function(file){
		const fsize = file.size;
		if (fsize >= MAX_FILE_SIZE){return false;}
		return true;
	};
	var showUploadError = function(error){
		errorBox.append('<span>' + error + '</span>');
	};
	var getForm = function(box){
		const formContainer = "<form enctype='multipart/form-data'></form>";
		return $(formContainer).html(box.clone());
	};
	var deleteFile = function(){
		const fileId = deleteModal.find('input[name="file_id"]').val();
		const fileRow = $('li[data-id="' + fileId + '"');
		fileRow.addClass( 'is-updating' );
		fileRow.removeClass( 'is-error' );

		let formContent = deleteModal.find('.modal-content');
		const deleteFileUrl = formContent.attr('action');
		let form = $("<form></form>").html(formContent.clone());

		// ajax request
		$.ajax({
			url: deleteFileUrl,
			type: 'POST',
			data: form.serialize(),
			beforeSend: function( xhr ) {
				deleteModal.modal('toggle');
			}
		})
		.done(function(response) {
			let isSuccess = response.success == true;
			if(isSuccess){ fileRow.fadeOut('slow').remove(); }
			else{ fileRow.addClass('is-error' ); }
			/// session timeout is not handled!!
		})
		.always(function(response) {
			fileRow.removeClass('is-updating');
			updateNoFileStatus();
		})
		.fail(function(response) {
			fileRow.addClass('is-error' );
		});
	};

	//Public API
	return {
		init: function(){
			deleteModal = $('#delete-file-modal');
			filesList = $('.uploaded-files ul');
			noFilesRow = filesList.find('li.empty-list');
			errorBox = $('.error-details');

			updateNoFileStatus();

			$('.delete-file-btn').on( 'click', function(){
				fileDeleteBtn = $(this);
				if( fileDeleteBtn.hasClass('is-deleting')) return false;
				fileDeleteBtn.addClass('is-deleting');
				deleteFile();
				fileDeleteBtn.removeClass('is-deleting');
			});

			$('.box').each( function( box ){
				var form 		 = $(this),
					uploadUrl	 = form.attr('action'),
					input		 = form.find('input[type="file"]'),
					inputName	 = input.attr('name'),
					label		 = form.find('label'),
					errorMsg	 = form.find('.box__error span'),
					restart		 = form.find('.box__restart'),
					resultBox	 = filesList,
					droppedFiles = false,
					startUploading	 = function(){
						form.addClass('is-uploading').removeClass('is-error');
						errorBox.empty();
					},
					formSubmit	 = function(){
						startUploading();
						errorBox.empty();

						var ajaxData = getUploadData();
						var isValidUploadSize = verifyUploadSize(ajaxData);

						if(!isValidUploadSize){
							form.addClass('is-error');
							showUploadError(FILE_SIZE_ERROR);
						}

						const isEmpty = ajaxData.getAll(inputName).length == 0;
						if(isEmpty){
							form.removeClass('is-uploading');
							return false;
						}
						getAjax().send(ajaxData);
					},
					showFiles	 = function(files){
						label.textContent = files.length > 1 ? (input.attr('data-multiple-caption') || '').replace('{count}', files.length) : files[0].name;
					},
					// triggerFormSubmit = function(){
					// 	var event = document.createEvent( 'HTMLEvents' );
					// 	event.initEvent( 'submit', true, false );
					// 	form.dispatchEvent( event );
					// },
					setupAdvancedForm = function(){
						form.addClass('has-advanced-upload'); // letting the CSS part to know drag&drop is supported by the browser

						['drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop'].forEach( function( event ){
							form.on(event, function(e){
								// preventing the unwanted behaviours
								e.preventDefault();
								e.stopPropagation();
							});
						});
						['dragover', 'dragenter'].forEach( function(event){
							form.on(event, function(){form.addClass('is-dragover');});
						});
						['dragleave', 'dragend', 'drop'].forEach( function(event){
							form.on(event, function(){form.removeClass('is-dragover');});
						});
						form.on('drop', function(e){
							e.preventDefault();
							droppedFiles = e.originalEvent.dataTransfer.files; // the files that were dropped
							showFiles(droppedFiles);
							formSubmit();
						});
					},
					getAjax = function(){
						var ajax = new XMLHttpRequest();
						ajax.open('POST', uploadUrl, true);

						ajax.onload = function(){
							form.removeClass( 'is-uploading' );
							if( ajax.status >= 200 && ajax.status < 400 ){
								let data = {};
								let error = '';
								let isSuccess = false;
								let files = false;
								try {
									data = JSON.parse( ajax.responseText );
									isSuccess = data.success == true;
									files = data.files;
									error = data.error;
								} catch (e) {
									error = 'Upload failed. You might have been logged out.';
									setTimeout(function(){
										window.location.reload();
									}, 3000);
								}

								if(files){
									showUploadedFiles(resultBox, files);
									//form.addClass('is-success');
								}
								else{
									form.addClass('is-error');
									showUploadError( error || 'Upload Failed. ');
								}
								updateNoFileStatus();
							}
							else {
								form.addClass('is-error');
								showUploadError('Error. ' + ajax.status + ': '+ ajax.responseText);
							}
						};

						ajax.onerror = function(){
							form.addClass('is-error').removeClass('is-uploading');
							showUploadError('Upload Request Failed.');
						};
						return ajax;
					},
					getUploadData = function(){
						var aForm = getForm(form);
						var ajaxData = new FormData( aForm[0] );

						if(droppedFiles){
							Array.prototype.forEach.call( droppedFiles, function( file ){
								ajaxData.append( inputName, file );
							});
						}
						return ajaxData;
					},
					verifyUploadSize = function(ajaxData){
						var isValidUploadSize = true;
						for(let [name, file] of ajaxData){
							if(!isValidFileSize(file)){
								isValidUploadSize = false;
								ajaxData.delete(name);
								//showUploadError(file.name + ' upload failed. ');
							}
						}
						return isValidUploadSize;
					};

				// drag&drop files if the feature is available
				if(isAdvancedUpload){ setupAdvancedForm(); }

				// automatically submit the form on file select
				input.on('change', function(e){
					showFiles(e.target.files);
					formSubmit();
				});

				// restart the form if has a state of error/success
				Array.prototype.forEach.call( restart, function(entry){
					$(entry).on('click', function(e){
						e.preventDefault();
						form.removeClass('is-error is-success');
					});
				});

				// Firefox focus bug fix for file input
				input.on('focus', function(){ input.addClass('has-focus'); });
				input.on('blur', function(){ input.removeClass('has-focus'); });
			});

			$(document).on('click', '.delete-file-link', function(e){
				let fileName = $(this).siblings('.file-name').text() || 'this file';
				let fileId = $(this).parent().attr('data-id');
				deleteModal.find('.file-name').text(fileName);
				deleteModal.find('input[name="file_id"]').val(fileId);
			});

			// wait for active delete action to complete
			deleteModal.on('show.bs.modal', function (e) {
				const rowsBeingUpdated = filesList.find('li.is-updating').length;
				if(rowsBeingUpdated >=1 ) {
					e.stopPropagation();
					return false;
				}
			});

			//Refresh modal
			deleteModal.on('close.bs.modal', function (e) {
				$(this).find('.file-name').text('this file');
			});
		}
	}
})();

