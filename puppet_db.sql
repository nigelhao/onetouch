-- phpMyAdmin SQL Dump
-- version 4.6.6deb4
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Feb 09, 2019 at 01:28 PM
-- Server version: 10.1.37-MariaDB-0+deb9u1
-- PHP Version: 7.0.33-0+deb9u1
-- Author: Nigel Chen Chin Hao

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `puppet_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `Change_Request`
--

CREATE TABLE `Change_Request` (
  `ID` int(11) NOT NULL,
  `RequestID` int(11) NOT NULL,
  `Date` varchar(50) NOT NULL,
  `Information` text NOT NULL,
  `Status` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `Machine`
--

CREATE TABLE `Machine` (
  `ID` int(11) NOT NULL,
  `VmName` varchar(100) NOT NULL,
  `CpuCore` int(11) NOT NULL,
  `MemorySize` int(11) NOT NULL,
  `StorageSize` int(11) NOT NULL,
  `Address` varchar(15) DEFAULT NULL,
  `Netmask` text,
  `Gateway` varchar(15) DEFAULT NULL,
  `Dns` varchar(15) DEFAULT NULL,
  `Hostname` varchar(200) NOT NULL,
  `CertName` varchar(200) DEFAULT NULL,
  `OperatingSystem` varchar(20) NOT NULL,
  `AdditionalRequirement` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `Request`
--

CREATE TABLE `Request` (
  `ID` int(11) NOT NULL,
  `UserID` int(11) NOT NULL,
  `MachineID` int(11) NOT NULL,
  `Status` int(11) NOT NULL,
  `Expiry` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `User`
--

CREATE TABLE `User` (
  `ID` int(11) NOT NULL,
  `Name` varchar(100) NOT NULL,
  `Email` varchar(200) NOT NULL,
  `Password` varchar(100) NOT NULL,
  `Role` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Change_Request`
--
ALTER TABLE `Change_Request`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `RequestID` (`RequestID`);

--
-- Indexes for table `Machine`
--
ALTER TABLE `Machine`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `Request`
--
ALTER TABLE `Request`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `UserID` (`UserID`),
  ADD KEY `MachineID` (`MachineID`);

--
-- Indexes for table `User`
--
ALTER TABLE `User`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `Change_Request`
--
ALTER TABLE `Change_Request`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `Machine`
--
ALTER TABLE `Machine`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `Request`
--
ALTER TABLE `Request`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `User`
--
ALTER TABLE `User`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;
--
-- Constraints for dumped tables
--

--
-- Constraints for table `Change_Request`
--
ALTER TABLE `Change_Request`
  ADD CONSTRAINT `Change_Request_ibfk_1` FOREIGN KEY (`RequestID`) REFERENCES `Request` (`ID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `Request`
--
ALTER TABLE `Request`
  ADD CONSTRAINT `Request_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`ID`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `Request_ibfk_2` FOREIGN KEY (`MachineID`) REFERENCES `Machine` (`ID`) ON DELETE CASCADE ON UPDATE CASCADE;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
