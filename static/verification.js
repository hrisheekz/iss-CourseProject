const video = document.getElementById('video');
const canvas = document.getElementById('capture-image');
const startBtn = document.getElementById('start-camera');
const captureBtn = document.getElementById('capture-frame');
const loginBtn = document.getElementById('login-button');

let capturedImage = null;

startBtn.addEventListener('click',async()=>{
    const stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.srcObject = stream
    if (typeof window.setCatStartled === 'function') window.setCatStartled();
})

captureBtn.addEventListener('click',()=>{
    const ctx = canvas.getContext("2d")
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    capturedImage = canvas.toDataURL("image/jpeg").split(",")[1]
    alert("Frame captured!")
})

loginBtn.addEventListener('click',async ()=>{
    if (!capturedImage){
        alert("Please capture a frame first!")
        return
    }
    const response = await fetch('/login',{
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({image:capturedImage})
    })
    const result = await response.json()
    if(result.success)
    {
        window.location.href = "/lobby"
    }
    else
    {
        alert("Face not recognized. Try again!")
    }
})