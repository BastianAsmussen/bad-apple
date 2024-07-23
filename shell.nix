let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (python-pkgs: [
      python-pkgs.opencv4
      python-pkgs.numpy
      python-pkgs.yt-dlp
      python-pkgs.pillow
    ]))
  ];
  
  nativeBuildInputs = with pkgs; [
    ffmpeg_7
  ];
}
