-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 10 Jun 2024 pada 18.01
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `resep_manajemen`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `resep_obat`
--

CREATE TABLE `resep_obat` (
  `id_resepobat` int(11) NOT NULL,
  `id_pasien` int(11) NOT NULL,
  `id_obat` int(11) NOT NULL,
  `jumlah_obat` int(11) NOT NULL,
  `nama_obat` varchar(255) NOT NULL,
  `keterangan_resep` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `resep_obat`
--

INSERT INTO `resep_obat` (`id_resepobat`, `id_pasien`, `id_obat`, `jumlah_obat`, `nama_obat`, `keterangan_resep`) VALUES
(1, 1, 101, 10, 'Paracetamol', 'Minum 1 tablet 3 kali sehari setelah makan'),
(2, 9, 101, 10, 'Panadol', 'Minum 1 tablet 3 kali sehari setelah makan'),
(3, 3, 103, 15, 'Ibuprofen', 'Minum 1 sendok teh sirup 3 kali sehari setelah makan'),
(4, 4, 104, 5, 'Betadine', 'Oleskan salep pada area yang terkena 2 kali sehari'),
(5, 5, 105, 30, 'Visine', 'Teteskan 2 tetes mata pada mata yang sakit 3 kali sehari'),
(6, 6, 106, 12, 'Cetirizine', 'Minum 1 tablet 2 kali sehari setelah makan'),
(7, 7, 107, 25, 'Omeprazole', 'Minum 1 kapsul setiap pagi setelah makan'),
(8, 8, 108, 18, 'Loratadine', 'Minum 1 sendok makan sirup 2 kali sehari sebelum tidur'),
(9, 9, 109, 8, 'Voltaren', 'Oleskan gel pada area yang terkena 3 kali sehari'),
(10, 10, 110, 22, 'Otipax', 'Teteskan 3 tetes telinga pada telinga yang sakit 2 kali sehari'),
(11, 9, 101, 10, 'Panadol', 'Minum 1 tablet 3 kali sehari setelah makan');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `resep_obat`
--
ALTER TABLE `resep_obat`
  ADD PRIMARY KEY (`id_resepobat`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `resep_obat`
--
ALTER TABLE `resep_obat`
  MODIFY `id_resepobat` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
