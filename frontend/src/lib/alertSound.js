let audioElement = null
let usingFallbackSrc = false

function playBeepFallback() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = ctx.createOscillator()
    const gain = ctx.createGain()

    oscillator.type = 'sine'
    oscillator.frequency.value = 880
    gain.gain.value = 0.15

    oscillator.connect(gain)
    gain.connect(ctx.destination)

    oscillator.start()
    oscillator.stop(ctx.currentTime + 0.35)
    oscillator.onended = () => ctx.close()
  } catch {
    // Audio not available
  }
}

function getAudio() {
  if (!audioElement) {
    audioElement = new Audio('/alert.mp3')
    audioElement.preload = 'auto'
  }
  return audioElement
}

export async function playAlertSound() {
  const audio = getAudio()

  try {
    audio.currentTime = 0
    await audio.play()
  } catch {
    if (!usingFallbackSrc) {
      usingFallbackSrc = true
      audio.src = '/alert.wav'
      try {
        audio.currentTime = 0
        await audio.play()
        return
      } catch {
        // fall through
      }
    }
    playBeepFallback()
  }
}
