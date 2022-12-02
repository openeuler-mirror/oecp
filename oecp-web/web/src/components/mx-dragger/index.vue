<template>
    <div class="page-draggle">
        <div :class="[borderhover?'draggle-area-active':'','draggle-area']" id="draggle-area">
            <slot></slot>
        </div>
    </div>
</template>
<script>
export default {
    data() {
        return {
            borderhover:false,
        }
    },
    methods:{
        dragenter(e){
            this.borderhover = true
            this.preventDefault(e)
        },
        dragleave(e){
            this.borderhover = false
            this.preventDefault(e)
        },
        dragover(e){
            this.borderhover = true
            this.preventDefault(e)
        },
        enentDrop(e){
            this.borderhover = false
            this.preventDefault(e)
            let fileData = e.dataTransfer.files;
            console.log(fileData);
            this.uploadFile(fileData)
        },
        preventDefault(e){
            e.stopPropagation();
            e.preventDefault();  //必填字段
        },
        uploadFile(file){
            let datas = new FormData();
            datas.append("file", file);
            console.log(file,'上传的文件，之后调用接口进行上传,入参的file为：'+datas,'文件类型为：'+file[0].type)
        }
    },
    mounted(){
        // 1.文件第一次进入拖动区时，触发 dragenter 事件
        // 2.文件在拖动区来回拖拽时，不断触发 dragover 事件
        // 3.文件已经在拖动区，并松开鼠标时，触发 drop 事件
        // 4.文件在拖动区来回拖拽时，不断触发dragleave 事件 
        var dropbox = document.getElementById('draggle-area');
        dropbox.addEventListener("drop",this.enentDrop,false)
        dropbox.addEventListener("dragleave",this.dragleave,false)
        dropbox.addEventListener("dragenter",this.dragenter,false)
        dropbox.addEventListener("dragover",this.dragover,false)
    }
}

</script>