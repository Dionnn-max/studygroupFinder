-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema study_group_finder
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema study_group_finder
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `study_group_finder` DEFAULT CHARACTER SET utf8 ;
USE `study_group_finder` ;

-- -----------------------------------------------------
-- Table `study_group_finder`.`students`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_group_finder`.`students` (
  `student_id` INT NOT NULL AUTO_INCREMENT,
  `student_email` VARCHAR(100) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `date_of_birth` DATE NOT NULL,
  `gender` VARCHAR(30) NOT NULL,
  `major` VARCHAR(100) NULL,
  `phone_number` VARCHAR(20) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`student_id`),
  UNIQUE INDEX `student_email_UNIQUE` (`student_email` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `study_group_finder`.`courses`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_group_finder`.`courses` (
  `course_id` INT NOT NULL AUTO_INCREMENT,
  `course_code` VARCHAR(20) NOT NULL,
  `course_name` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`course_id`),
  UNIQUE INDEX `course_code_UNIQUE` (`course_code` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `study_group_finder`.`enrollments`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_group_finder`.`enrollments` (
  `student_id` INT NOT NULL,
  `course_id` INT NOT NULL,
  `added_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`student_id`, `course_id`),
  INDEX `fk_enrollments_course_idx` (`course_id` ASC) VISIBLE,
  CONSTRAINT `fk_enrollments_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `study_group_finder`.`students` (`student_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_enrollments_course`
    FOREIGN KEY (`course_id`)
    REFERENCES `study_group_finder`.`courses` (`course_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `study_group_finder`.`study_groups`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_group_finder`.`study_groups` (
  `group_id` INT NOT NULL AUTO_INCREMENT,
  `course_id` INT NOT NULL,
  `creator_id` INT NOT NULL,
  `leader_id` INT NOT NULL,
  `group_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `meeting_format` ENUM('in_person', 'online', 'hybrid') NOT NULL,
  `meeting_location` VARCHAR(255) NULL,
  `maximum_capacity` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`group_id`),
  INDEX `fk_study_groups_course_idx` (`course_id` ASC) VISIBLE,
  INDEX `fk_study_groups_creator_idx` (`creator_id` ASC) VISIBLE,
  INDEX `fk_study_groups_leader_idx` (`leader_id` ASC) VISIBLE,
  UNIQUE INDEX `uq_study_groups_creator_course` (`creator_id` ASC, `course_id` ASC) VISIBLE,
  CONSTRAINT `fk_study_groups_course`
    FOREIGN KEY (`course_id`)
    REFERENCES `study_group_finder`.`courses` (`course_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_study_groups_creator`
    FOREIGN KEY (`creator_id`)
    REFERENCES `study_group_finder`.`students` (`student_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_study_groups_leader`
    FOREIGN KEY (`leader_id`)
    REFERENCES `study_group_finder`.`students` (`student_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `study_group_finder`.`group_members`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_group_finder`.`group_members` (
  `group_id` INT NOT NULL,
  `student_id` INT NOT NULL,
  `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`group_id`, `student_id`),
  INDEX `fk_group_members_student_idx` (`student_id` ASC) VISIBLE,
  CONSTRAINT `fk_group_members_group`
    FOREIGN KEY (`group_id`)
    REFERENCES `study_group_finder`.`study_groups` (`group_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_group_members_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `study_group_finder`.`students` (`student_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `study_group_finder`.`group_meeting_times`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_group_finder`.`group_meeting_times` (
  `group_id` INT NOT NULL,
  `day_of_week` ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday') NOT NULL,
  `start_time` TIME NOT NULL,
  `end_time` TIME NOT NULL,
  PRIMARY KEY (`group_id`, `day_of_week`, `start_time`),
  CONSTRAINT `fk_meeting_times_group`
    FOREIGN KEY (`group_id`)
    REFERENCES `study_group_finder`.`study_groups` (`group_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
